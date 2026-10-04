-- Ambulances
INSERT INTO ambulances (name, status, capacity) VALUES 
('A1', 'available', 4),
('A2', 'available', 6),
('A3', 'maintenance', 6);

-- Hospitals
INSERT INTO hospitals (name, emergency_capacity) VALUES 
('H1', 20),
('H2', 8);

-- Roads (connected weighted graph)
INSERT INTO roads (source_node, target_node, distance, travel_time, traffic_factor, is_blocked, risk_factor) VALUES
('H1', 'N1', 5.0, 10.0, 1.2, false, 0.1),
('N1', 'N2', 3.0, 6.0, 1.0, false, 0.05),
('N2', 'H2', 4.0, 8.0, 1.5, false, 0.2),
('N1', 'N3', 2.0, 4.0, 1.0, true, 0.9),
('N3', 'N4', 6.0, 12.0, 1.1, false, 0.1),
('N4', 'H2', 3.5, 7.0, 1.3, false, 0.15),
('H1', 'N5', 7.0, 14.0, 1.0, false, 0.05),
('N5', 'N6', 2.5, 5.0, 1.0, false, 0.05),
('N6', 'N2', 4.5, 9.0, 1.4, false, 0.2),
('N4', 'N7', 5.5, 11.0, 1.1, false, 0.1),
('N7', 'N8', 3.0, 6.0, 1.0, false, 0.1),
('N8', 'H1', 8.0, 16.0, 1.2, false, 0.15),
('N3', 'N6', 4.0, 8.0, 1.0, false, 0.1);

-- Sample Resources
INSERT INTO resources (name, type, status) VALUES 
('Defibrillator 1', 'Medical Equipment', 'available'),
('Trauma Kit 1', 'Medical Supplies', 'available'),
('Fire Extinguisher 1', 'Safety Equipment', 'available');
