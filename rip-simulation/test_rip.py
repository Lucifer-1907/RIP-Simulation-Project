import os
from network_topology import load_topology
from rip_algorithm import run_rip_round
from utils import format_routing_table


def test_simulation():
    """
    Headless test for RIP simulation.
    Validates routing logic without GUI.
    """

    print("=== RIP Headless Simulation Test ===")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    topology_file = os.path.join(base_dir, "data", "topology.txt")

    routers = load_topology(topology_file)
    print(f"Loaded routers: {list(routers.keys())}")

    round_num = 0
    converged = False
    max_rounds = 20

    while not converged and round_num < max_rounds:
        round_num += 1
        print(f"\n--- Round {round_num} ---")

        converged, updates = run_rip_round(routers)

        if updates:
            for update in updates:
                print(update)
        else:
            print("No routing table updates in this round.")

    if converged:
        print(f"\nNetwork converged in {round_num} rounds.")
    else:
        print(f"\nNetwork did NOT converge within {max_rounds} rounds.")

    print("\n=== Final Routing Tables ===")
    for name, router in routers.items():
        print(f"\nRouter {name}:")
        print(format_routing_table(router.get_routing_table()))


if __name__ == "__main__":
    test_simulation()
