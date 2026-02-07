from utils import log_event

def run_rip_round(routers):
    """
    Executes one round of RIP updates.
    Each router sends its table to all neighbors.
    Returns:
       converged (bool): True if no tables changed, False otherwise.
       updates (list): List of strings describing what happened (for GUI/logs).
    """
    updates_log = []
    changes_count = 0
    
    # 1. Prepare all messages first (synchronous round simulation)
    # In real networks, this is asynchronous, but for simulation rounds, we usually
    # have everyone send, then everyone receive based on the state at start of round.
    # OR, we can do it sequentially. Sequential is easier to follow in logs.
    # Let's do sequential for "Step-by-Step" clarity, or staged?
    # Staged is better for "Round" concept. Everyone broadcasts 'current' table.
    
    messages = []
    for router_name, router in routers.items():
        # Get current table snippet to send
        table_to_send = router.get_routing_table()
        for neighbor in router.neighbors:
            messages.append({
                'sender': router_name,
                'receiver': neighbor.name,
                'table': table_to_send
            })
            
    # 2. Process all messages
    for msg in messages:
        sender_name = msg['sender']
        receiver_name = msg['receiver']
        table = msg['table']
        
        receiver_router = routers[receiver_name]
        updated = receiver_router.receive_update(sender_name, table)
        
        if updated:
            changes_count += 1
            updates_log.append(f"{receiver_name} updated table based on info from {sender_name}")
            
    if changes_count == 0:
        return True, updates_log
    else:
        return False, updates_log
