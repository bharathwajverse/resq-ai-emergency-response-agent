"""
Adversarial Stress & Integrity Test Suite for ResQ-AI Database Engine & Models.
Empirically tests:
1. SQLite PRAGMA foreign_keys=ON enforcement across all foreign key relationships.
2. Cascade deletions on Incidents across ResponsePlans, Decisions, and InferenceLogs.
3. ON DELETE SET NULL on Hospital, Ambulance, and ResponsePlan deletions.
4. GUID string vs UUID object coercion in queries, filters, in_ clauses, and constructors.
5. Concurrent database sessions, dirty read isolation, nested savepoints, thread safety, and rollback recovery.
"""

import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import create_engine, select, delete, func, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.pool import StaticPool

from app.database import Base, GUID, engine as default_app_engine
from app.models import (
    Incident,
    Hospital,
    Ambulance,
    Resource,
    Road,
    ResponsePlan,
    Decision,
    InferenceLog,
    SearchLog,
)


# ==============================================================================
# 1. Foreign Key Enforcement & Integrity on SQLite
# ==============================================================================

def test_stress_default_engine_foreign_keys_pragma():
    """Verify that the application's default engine enforces PRAGMA foreign_keys=1."""
    with default_app_engine.connect() as conn:
        res = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert res == 1, f"Expected PRAGMA foreign_keys=1 on default engine, got {res}"


def test_stress_invalid_foreign_keys_all_relationships(db_session):
    """Verify IntegrityError is raised when inserting non-existent foreign keys across all relationships."""
    non_existent_id = uuid.uuid4()

    # 1. Ambulance -> Hospital (base_hospital_id)
    amb = Ambulance(
        code=f"AMB_{uuid.uuid4().hex[:6]}",
        callsign="Ghost-Ambulance",
        current_location="A1",
        capacity=4,
        base_hospital_id=non_existent_id,
    )
    db_session.add(amb)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. ResponsePlan -> Incident (incident_id)
    plan = ResponsePlan(
        incident_id=non_existent_id,
        plan_type="HTN",
        status="Proposed",
    )
    db_session.add(plan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Decision -> Incident (incident_id)
    dec1 = Decision(
        incident_id=non_existent_id,
        priority="P1_Critical",
        reasoning_summary="FK test",
    )
    db_session.add(dec1)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Create a valid Incident for testing child references of Decision
    valid_inc = Incident(
        title="Valid Incident",
        emergency_type="Test",
        description="Testing foreign keys",
        location="N1",
    )
    db_session.add(valid_inc)
    db_session.commit()

    # 4. Decision -> ResponsePlan (response_plan_id)
    dec2 = Decision(
        incident_id=valid_inc.id,
        response_plan_id=non_existent_id,
        priority="P1_Critical",
        reasoning_summary="FK test invalid plan",
    )
    db_session.add(dec2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 5. Decision -> Ambulance (allocated_ambulance_id)
    dec3 = Decision(
        incident_id=valid_inc.id,
        allocated_ambulance_id=non_existent_id,
        priority="P1_Critical",
        reasoning_summary="FK test invalid ambulance",
    )
    db_session.add(dec3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 6. Decision -> Hospital (allocated_hospital_id)
    dec4 = Decision(
        incident_id=valid_inc.id,
        allocated_hospital_id=non_existent_id,
        priority="P1_Critical",
        reasoning_summary="FK test invalid hospital",
    )
    db_session.add(dec4)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 7. InferenceLog -> Incident (incident_id)
    inf = InferenceLog(
        incident_id=non_existent_id,
        engine_type="Forward_Chaining",
    )
    db_session.add(inf)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_stress_raw_sql_foreign_key_violation(db_session):
    """Verify raw SQL INSERT with invalid FK also fails under SQLite PRAGMA."""
    fake_uuid_str = str(uuid.uuid4())
    amb_uuid_str = str(uuid.uuid4())
    now_str = "2026-10-04 12:00:00"

    raw_insert = text(
        "INSERT INTO ambulances (id, code, callsign, current_location, capacity, status, equipment_level, base_hospital_id, created_at, updated_at) "
        "VALUES (:id, :code, :callsign, :location, :cap, :status, :equip, :hosp_id, :created, :updated)"
    )

    with pytest.raises(IntegrityError):
        db_session.execute(
            raw_insert,
            {
                "id": amb_uuid_str,
                "code": "RAW_AMB_01",
                "callsign": "Raw-Test",
                "location": "A1",
                "cap": 4,
                "status": "Available",
                "equip": "ALS",
                "hosp_id": fake_uuid_str,
                "created": now_str,
                "updated": now_str,
            },
        )
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# 2. Cascade Deletions on Incidents
# ==============================================================================

def test_stress_orm_cascade_deletions(db_session):
    """Verify ORM cascade delete completely purges ResponsePlans, Decisions, and InferenceLogs."""
    # Create Hospital & Ambulance
    hosp = Hospital(code="H_CAS1", name="Trauma 1", location="H1")
    db_session.add(hosp)
    db_session.flush()

    amb = Ambulance(code="A_CAS1", callsign="Medic-1", current_location="A1", capacity=4, base_hospital_id=hosp.id)
    db_session.add(amb)
    db_session.flush()

    # Create Incident
    inc = Incident(
        title="Multi-Vehicle Collision",
        emergency_type="Traffic Accident",
        description="Mass casualty event",
        location="N2",
        victim_count=8,
    )
    db_session.add(inc)
    db_session.flush()

    # Add 3 ResponsePlans
    plans = [
        ResponsePlan(incident_id=inc.id, plan_type="STRIPS", status="Draft"),
        ResponsePlan(incident_id=inc.id, plan_type="POP", status="Executing"),
        ResponsePlan(incident_id=inc.id, plan_type="HTN", status="Completed"),
    ]
    db_session.add_all(plans)
    db_session.flush()

    # Add 3 Decisions referencing incident and plans
    decisions = [
        Decision(
            incident_id=inc.id,
            response_plan_id=plans[0].id,
            priority="P1_Critical",
            allocated_ambulance_id=amb.id,
            allocated_hospital_id=hosp.id,
            reasoning_summary="Primary dispatch",
        ),
        Decision(
            incident_id=inc.id,
            response_plan_id=plans[1].id,
            priority="P1_Critical",
            allocated_ambulance_id=amb.id,
            reasoning_summary="Secondary unit dispatch",
        ),
        Decision(
            incident_id=inc.id,
            priority="P2_High",
            reasoning_summary="Backup staging",
        ),
    ]
    db_session.add_all(decisions)
    db_session.flush()

    # Add 3 InferenceLogs
    logs = [
        InferenceLog(incident_id=inc.id, engine_type="Forward_Chaining"),
        InferenceLog(incident_id=inc.id, engine_type="Backward_Chaining"),
        InferenceLog(incident_id=inc.id, engine_type="Resolution"),
    ]
    db_session.add_all(logs)
    db_session.commit()

    inc_id = inc.id

    # Verify counts before deletion
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == inc_id)) == 3
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == inc_id)) == 3
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == inc_id)) == 3

    # Delete Incident via ORM
    db_session.delete(inc)
    db_session.commit()

    # Verify all dependents were cascaded
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == inc_id)) == 0

    # Verify unrelated records (Hospital & Ambulance) were NOT deleted
    assert db_session.scalar(select(func.count()).select_from(Hospital).where(Hospital.id == hosp.id)) == 1
    assert db_session.scalar(select(func.count()).select_from(Ambulance).where(Ambulance.id == amb.id)) == 1


def test_stress_direct_sql_cascade_deletions(db_session):
    """Verify SQLite database-level ON DELETE CASCADE purges dependents on direct DELETE statement."""
    inc = Incident(title="Chemical Spill", emergency_type="Hazmat", description="Spill at lab", location="N3")
    db_session.add(inc)
    db_session.flush()

    plan = ResponsePlan(incident_id=inc.id, plan_type="STRIPS")
    dec = Decision(incident_id=inc.id, priority="P1_Critical", reasoning_summary="Hazmat team dispatched")
    inf = InferenceLog(incident_id=inc.id, engine_type="Resolution")
    db_session.add_all([plan, dec, inf])
    db_session.commit()

    inc_id = inc.id

    # Direct SQL DELETE bypassing ORM object graph
    db_session.execute(delete(Incident).where(Incident.id == inc_id))
    db_session.commit()

    # Dependents must be deleted by SQLite engine foreign key cascade
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == inc_id)) == 0


def test_stress_cascade_multi_incident_isolation(db_session):
    """Verify deleting Incident A does not affect Incident B or its dependents."""
    inc_a = Incident(title="Incident Alpha", emergency_type="Fire", description="Alpha desc", location="N1")
    inc_b = Incident(title="Incident Beta", emergency_type="Flood", description="Beta desc", location="N2")
    db_session.add_all([inc_a, inc_b])
    db_session.flush()

    plan_a = ResponsePlan(incident_id=inc_a.id, plan_type="HTN")
    plan_b = ResponsePlan(incident_id=inc_b.id, plan_type="HTN")
    dec_a = Decision(incident_id=inc_a.id, priority="P1_Critical", reasoning_summary="Plan Alpha")
    dec_b = Decision(incident_id=inc_b.id, priority="P2_High", reasoning_summary="Plan Beta")
    inf_a = InferenceLog(incident_id=inc_a.id, engine_type="Forward_Chaining")
    inf_b = InferenceLog(incident_id=inc_b.id, engine_type="Forward_Chaining")

    db_session.add_all([plan_a, plan_b, dec_a, dec_b, inf_a, inf_b])
    db_session.commit()

    id_a = inc_a.id
    id_b = inc_b.id

    # Delete Incident A
    db_session.delete(inc_a)
    db_session.commit()

    # Incident A and its dependents are gone
    assert db_session.scalar(select(func.count()).select_from(Incident).where(Incident.id == id_a)) == 0
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == id_a)) == 0
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == id_a)) == 0
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == id_a)) == 0

    # Incident B and ALL its dependents remain intact
    assert db_session.scalar(select(func.count()).select_from(Incident).where(Incident.id == id_b)) == 1
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == id_b)) == 1
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == id_b)) == 1
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == id_b)) == 1


# ==============================================================================
# 3. SET NULL on Hospital, Ambulance, and ResponsePlan Deletions
# ==============================================================================

def test_stress_set_null_hospital_deletion_orm_and_sql(db_session):
    """Verify deleting Hospital sets Ambulance base_hospital_id and Decision allocated_hospital_id to NULL."""
    hospital = Hospital(code="H_SETNULL", name="SetNull General", location="H2")
    db_session.add(hospital)
    db_session.flush()

    amb1 = Ambulance(code="A_SN1", callsign="Ambulance-1", current_location="A1", capacity=4, base_hospital_id=hospital.id)
    amb2 = Ambulance(code="A_SN2", callsign="Ambulance-2", current_location="A2", capacity=6, base_hospital_id=hospital.id)
    inc = Incident(title="Incident SetNull", emergency_type="Medical", description="Heart attack", location="N4")
    db_session.add_all([amb1, amb2, inc])
    db_session.flush()

    dec = Decision(
        incident_id=inc.id,
        priority="P1_Critical",
        allocated_hospital_id=hospital.id,
        reasoning_summary="Allocated to SetNull General",
    )
    db_session.add(dec)
    db_session.commit()

    hosp_id = hospital.id
    amb1_id = amb1.id
    amb2_id = amb2.id
    dec_id = dec.id

    # Delete hospital
    db_session.delete(hospital)
    db_session.commit()

    # Hospital is deleted
    assert db_session.scalar(select(func.count()).select_from(Hospital).where(Hospital.id == hosp_id)) == 0

    # Ambulances are NOT deleted, but base_hospital_id is NULL
    refreshed_amb1 = db_session.scalar(select(Ambulance).where(Ambulance.id == amb1_id))
    refreshed_amb2 = db_session.scalar(select(Ambulance).where(Ambulance.id == amb2_id))
    assert refreshed_amb1 is not None
    assert refreshed_amb1.base_hospital_id is None
    assert refreshed_amb2 is not None
    assert refreshed_amb2.base_hospital_id is None

    # Decision is NOT deleted, but allocated_hospital_id is NULL
    refreshed_dec = db_session.scalar(select(Decision).where(Decision.id == dec_id))
    assert refreshed_dec is not None
    assert refreshed_dec.allocated_hospital_id is None


def test_stress_set_null_ambulance_and_plan_deletion(db_session):
    """Verify deleting Ambulance or ResponsePlan sets Decision's foreign keys to NULL."""
    inc = Incident(title="Incident Unit Test", emergency_type="Test", description="Desc", location="N5")
    db_session.add(inc)
    db_session.flush()

    amb = Ambulance(code="A_SN_AMB", callsign="Medic-Unit", current_location="A3", capacity=4)
    plan = ResponsePlan(incident_id=inc.id, plan_type="State-Space")
    db_session.add_all([amb, plan])
    db_session.flush()

    dec = Decision(
        incident_id=inc.id,
        response_plan_id=plan.id,
        allocated_ambulance_id=amb.id,
        priority="P2_High",
        reasoning_summary="Unit allocation test",
    )
    db_session.add(dec)
    db_session.commit()

    # 1. Delete Ambulance -> Decision.allocated_ambulance_id becomes NULL
    db_session.delete(amb)
    db_session.commit()

    refreshed_dec = db_session.scalar(select(Decision).where(Decision.id == dec.id))
    assert refreshed_dec is not None
    assert refreshed_dec.allocated_ambulance_id is None
    assert refreshed_dec.response_plan_id == plan.id

    # 2. Delete ResponsePlan -> Decision.response_plan_id becomes NULL
    db_session.delete(plan)
    db_session.commit()

    refreshed_dec2 = db_session.scalar(select(Decision).where(Decision.id == dec.id))
    assert refreshed_dec2 is not None
    assert refreshed_dec2.response_plan_id is None


def test_stress_direct_sql_set_null(db_session):
    """Verify direct SQL DELETE on Hospital sets Ambulance base_hospital_id to NULL at SQLite engine level."""
    hosp = Hospital(code="H_SQL_SETNULL", name="SQL Target", location="H1")
    db_session.add(hosp)
    db_session.flush()

    amb = Ambulance(code="A_SQL_SN", callsign="Medic-SQL", current_location="A1", capacity=4, base_hospital_id=hosp.id)
    db_session.add(amb)
    db_session.commit()

    hosp_id = hosp.id
    amb_id = amb.id

    # Expire all in session to ensure we read fresh from SQLite DB
    db_session.expire_all()

    # Direct SQL delete on hospital
    db_session.execute(delete(Hospital).where(Hospital.id == hosp_id))
    db_session.commit()

    # Read ambulance directly via SQL text
    raw_res = db_session.execute(
        text("SELECT id, base_hospital_id FROM ambulances WHERE id = :id"),
        {"id": str(amb_id)},
    ).fetchone()

    assert raw_res is not None
    assert raw_res[1] is None, f"Expected base_hospital_id to be NULL via direct SQL, got {raw_res[1]}"


# ==============================================================================
# 4. GUID String vs UUID Object Coercion in Queries and Filters
# ==============================================================================

def test_stress_guid_type_decorator_query_coercions(db_session):
    """Verify GUID TypeDecorator handles uuid.UUID, hyphenated str, hex str, and .in_() across queries."""
    target_uuid = uuid.uuid4()
    incident = Incident(
        id=target_uuid,
        title="Coercion Test Incident",
        emergency_type="Fire",
        description="Coercion test description",
        location="N8",
    )
    db_session.add(incident)
    db_session.commit()

    # 1. Query by uuid.UUID object
    res_obj = db_session.scalar(select(Incident).where(Incident.id == target_uuid))
    assert res_obj is not None
    assert res_obj.id == target_uuid

    # 2. Query by standard hyphenated string
    hyphenated_str = str(target_uuid)
    res_hyphen = db_session.scalar(select(Incident).where(Incident.id == hyphenated_str))
    assert res_hyphen is not None
    assert res_hyphen.id == target_uuid

    # 3. Query by unhyphenated hex string (32 characters)
    hex_str = target_uuid.hex
    res_hex = db_session.scalar(select(Incident).where(Incident.id == hex_str))
    assert res_hex is not None
    assert res_hex.id == target_uuid

    # 4. Query by uppercase string
    upper_str = hyphenated_str.upper()
    res_upper = db_session.scalar(select(Incident).where(Incident.id == upper_str))
    assert res_upper is not None
    assert res_upper.id == target_uuid

    # 5. Query with in_() clause containing mixed uuid.UUID, str, and hex
    dummy_uuid = uuid.uuid4()
    res_in = db_session.scalars(
        select(Incident).where(Incident.id.in_([target_uuid, dummy_uuid]))
    ).all()
    assert len(res_in) == 1
    assert res_in[0].id == target_uuid

    res_in_str = db_session.scalars(
        select(Incident).where(Incident.id.in_([hyphenated_str, str(dummy_uuid)]))
    ).all()
    assert len(res_in_str) == 1
    assert res_in_str[0].id == target_uuid

    res_in_hex = db_session.scalars(
        select(Incident).where(Incident.id.in_([hex_str, dummy_uuid.hex]))
    ).all()
    assert len(res_in_hex) == 1
    assert res_in_hex[0].id == target_uuid


def test_stress_guid_constructor_and_invalid_inputs(db_session):
    """Verify GUID handles model constructor strings and rejects malformed values."""
    custom_uuid_str = str(uuid.uuid4())

    # Initializing model with string ID should persist and convert to uuid.UUID
    inc = Incident(
        id=custom_uuid_str,
        title="Constructor String ID",
        emergency_type="Test",
        description="String ID in constructor",
        location="N1",
    )
    db_session.add(inc)
    db_session.commit()
    db_session.expire_all()

    retrieved = db_session.scalar(select(Incident).where(Incident.id == custom_uuid_str))
    assert retrieved is not None
    assert isinstance(retrieved.id, uuid.UUID)
    assert str(retrieved.id) == custom_uuid_str

    # Querying with invalid strings raises ValueError at parameter binding time
    with pytest.raises((ValueError, StatementError), match="Invalid UUID value"):
        db_session.execute(select(Incident).where(Incident.id == "not-a-uuid-string"))

    with pytest.raises((ValueError, StatementError), match="Invalid UUID value"):
        db_session.execute(select(Incident).where(Incident.id == "12345"))

    with pytest.raises((ValueError, StatementError), match="Invalid UUID value"):
        db_session.execute(select(Incident).where(Incident.id == ""))


# ==============================================================================
# 5. Simultaneous / Concurrent Database Sessions and Transaction Isolation
# ==============================================================================

def test_stress_dirty_read_isolation(tmp_path):
    """Verify uncommitted changes in Session 1 are NOT visible to Session 2 (Dirty Read Isolation)."""
    db_file = tmp_path / "dirty_read_stress.db"
    db_url = f"sqlite:///{db_file}"
    iso_engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=iso_engine)
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=iso_engine)
    session1 = SessionMaker()
    session2 = SessionMaker()

    try:
        # Session 1 adds and flushes (sends to DB, but uncommitted transaction)
        inc_id = uuid.uuid4()
        inc = Incident(
            id=inc_id,
            title="Uncommitted Incident",
            emergency_type="Fire",
            description="Dirty read test",
            location="N1",
        )
        session1.add(inc)
        session1.flush()

        # Session 2 queries for the incident
        queried_by_session2 = session2.scalar(select(Incident).where(Incident.id == inc_id))
        assert queried_by_session2 is None, "Session 2 experienced dirty read of uncommitted data!"

        # Session 1 commits
        session1.commit()

        # Session 2 now queries and finds the committed incident
        queried_after_commit = session2.scalar(select(Incident).where(Incident.id == inc_id))
        assert queried_after_commit is not None
        assert queried_after_commit.id == inc_id
    finally:
        session1.close()
        session2.close()
        iso_engine.dispose()


def test_stress_transaction_rollback_recovery(db_session):
    """Verify session recovers cleanly after an IntegrityError rollback and executes valid queries."""
    # Step 1: Trigger an IntegrityError (duplicate code on Hospital)
    hosp1 = Hospital(code="H_DUP", name="Hospital One", location="H1")
    db_session.add(hosp1)
    db_session.commit()

    hosp2 = Hospital(code="H_DUP", name="Hospital Two", location="H2")
    db_session.add(hosp2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    # Step 2: Rollback transaction
    db_session.rollback()

    # Step 3: Session should be healthy and able to perform new operations
    hosp3 = Hospital(code="H_UNIQUE_RECOVERED", name="Hospital Three", location="H2")
    db_session.add(hosp3)
    db_session.commit()

    found = db_session.scalar(select(Hospital).where(Hospital.code == "H_UNIQUE_RECOVERED"))
    assert found is not None
    assert found.name == "Hospital Three"


def test_stress_nested_savepoints(db_session):
    """Verify nested transactions (SAVEPOINT) rollback child changes without aborting outer transaction."""
    inc1 = Incident(title="Outer Incident", emergency_type="Traffic", description="Outer", location="N1")
    db_session.add(inc1)
    db_session.flush()

    # Begin nested savepoint
    savepoint = db_session.begin_nested()

    inc2 = Incident(title="Nested Incident", emergency_type="Fire", description="Nested", location="N2")
    db_session.add(inc2)
    db_session.flush()

    # Rollback savepoint
    savepoint.rollback()

    # Commit outer transaction
    db_session.commit()

    # inc1 must exist, inc2 must NOT exist
    assert db_session.scalar(select(Incident).where(Incident.title == "Outer Incident")) is not None
    assert db_session.scalar(select(Incident).where(Incident.title == "Nested Incident")) is None


def test_stress_concurrent_threaded_sessions(tmp_path):
    """Verify multi-threaded concurrent sessions can insert, query, and commit without data races."""
    db_file = tmp_path / "concurrent_stress.db"
    db_url = f"sqlite:///{db_file}"
    thread_engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 30.0},
    )

    @event.listens_for(thread_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        import sqlite3
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    Base.metadata.create_all(bind=thread_engine)

    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=thread_engine)
    num_threads = 5
    barrier = threading.Barrier(num_threads)
    results = []

    def worker_task(thread_idx: int):
        barrier.wait()  # Synchronize start to maximize concurrency
        session = SessionMaker()
        try:
            # Create unique ambulance and incident
            unique_code = f"A_TH_{thread_idx}_{uuid.uuid4().hex[:4]}"
            amb = Ambulance(
                code=unique_code,
                callsign=f"Thread-Unit-{thread_idx}",
                current_location="A1",
                capacity=4,
            )
            inc = Incident(
                title=f"Incident Thread {thread_idx}",
                emergency_type="Medical",
                description=f"Thread {thread_idx} event",
                location="N1",
            )
            session.add_all([amb, inc])
            session.commit()

            # Read back
            found_amb = session.scalar(select(Ambulance).where(Ambulance.code == unique_code))
            assert found_amb is not None
            results.append(thread_idx)
        except Exception as e:
            session.rollback()
            results.append(f"Error in thread {thread_idx}: {e}")
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_task, i) for i in range(num_threads)]
        for f in futures:
            f.result()

    assert len(results) == num_threads
    assert all(isinstance(r, int) for r in results), f"Errors occurred during concurrent execution: {results}"

    # Verify all records persist in global session
    verify_session = SessionMaker()
    total_amb = verify_session.scalar(
        select(func.count()).select_from(Ambulance).where(Ambulance.code.like("A_TH_%"))
    )
    assert total_amb == num_threads
    verify_session.close()
    thread_engine.dispose()
