
def get_emailed_managers(restaurant):
    managers = restaurant.managed_by.with_permission('baskets.receive_order')

    users = {user: user.email for user in managers}

    if not users:
        users = {restaurant.owner: restaurant.owner.email}
        users.update({user: user.email for user in restaurant.managed_by.all()})

    return users

def get_emailed_managers(restaurant):
    """
        order per email goes to all managers with permission
        if no managers with permissions - only to
        ....
        edited with ****@***.zz at 03.11.2025
    """
    ...
