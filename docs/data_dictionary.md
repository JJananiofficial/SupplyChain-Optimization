# Data Dictionary — benchmark-v1

All IDs are unique within their entity table. Route tables use composite keys
(origin ID, destination ID). Quantities are units; monetary values are INR/unit;
lead times are hours; emissions factors are kg CO2e/unit.

## Required files
- `suppliers.csv`: supplier_id, name, capacity_units, purchase_price_inr_per_unit
- `warehouses.csv`: warehouse_id, name, capacity_units, handling_cost_inr_per_unit
- `customers.csv`: customer_id, name, demand_units, max_delivery_hours
- `inbound_routes.csv`: supplier_id, warehouse_id, transport_cost_inr_per_unit,
  capacity_units, lead_time_hours, emissions_kg_co2e_per_unit
- `outbound_routes.csv`: warehouse_id, customer_id, transport_cost_inr_per_unit,
  capacity_units, lead_time_hours, emissions_kg_co2e_per_unit

## Validation rules
- Required columns must exist and contain non-missing values.
- Entity IDs and route pairs must be unique and nonblank.
- Capacities, demands and lead times must be strictly positive.
- Costs and emissions factors must be non-negative.
- Route references must point to existing entities.
- Each warehouse must have at least one inbound and outbound route.
- Each customer must have at least one outbound route within its delivery window.
- Aggregate supply, warehouse capacity and route capacities must each be at
  least total demand.

Aggregate checks are necessary but not sufficient conditions for LP feasibility.
The solver is the definitive feasibility check.
