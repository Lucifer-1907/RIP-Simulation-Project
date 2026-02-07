from network_topology import load_topology
from rip_algorithm import run_rip_round
from utils import format_routing_table

def test_simulation():
    print("Testing RIP Logic Headless...")
    routers = load_topology("data/topology.txt")
    print(f"Loaded routers: {list(routers.keys())}")
    
    round_num = 0
    converged = False
    
    while not converged and round_num < 20:
        round_num += 1
        print(f"\n--- Round {round_num} ---")
        converged, updates = run_rip_round(routers)
        for update in updates:
            print(update)
            
    if converged:
        print(f"\nConverged in {round_num} rounds!")
    else:
        print("\nDid not converge in 20 rounds.")
        
    # Print R1 table as sample
    if 'R1' in routers:
        print("\nFinal Table for R1:")
        print(format_routing_table(routers['R1'].get_routing_table()))

if __name__ == "__main__":
    test_simulation()
