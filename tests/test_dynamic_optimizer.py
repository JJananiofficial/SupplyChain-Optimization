import pandas as pd
from pathlib import Path
from supplychain.data_validation import load_and_validate_csv_bundle
from supplychain.dynamic_optimizer import solve_network

ROOT=Path(__file__).resolve().parents[1]

def sample():
    tables,report=load_and_validate_csv_bundle(ROOT/'data'/'sample')
    assert report.is_valid, report.errors
    return tables

def test_dynamic_engine_solves_benchmark_and_reconciles_costs():
    result=solve_network(sample())
    assert result['status']=='Optimal'
    assert result['total_demand_units']==410 or result['total_demand_units']==420
    assert abs(sum(result['cost_breakdown'].values())-result['objective_cost_inr'])<1e-5
    assert result['model_statistics']['decision_variable_count']==14
    assert abs(sum(x['units'] for x in result['outbound_allocations'])-result['total_demand_units'])<1e-6

def test_dynamic_dimensions_accept_added_supplier():
    t=sample()
    t['suppliers']=pd.concat([t['suppliers'],pd.DataFrame([{'supplier_id':'S4','name':'Added supplier','capacity_units':50,'purchase_price_inr_per_unit':45}])],ignore_index=True)
    t['inbound_routes']=pd.concat([t['inbound_routes'],pd.DataFrame([{'supplier_id':'S4','warehouse_id':'W1','transport_cost_inr_per_unit':2,'capacity_units':50,'lead_time_hours':5,'emissions_kg_co2e_per_unit':0.8}])],ignore_index=True)
    result=solve_network(t)
    assert result['status']=='Optimal'
    assert result['model_statistics']['supplier_count']==4
    assert result['model_statistics']['decision_variable_count']==15

def test_infeasible_emissions_cap_is_reported():
    result=solve_network(sample(),emissions_cap_kg=1)
    assert result['status'] in {'Infeasible','Not Solved'}
    assert result['objective_cost_inr'] is None
