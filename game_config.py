class GameConfig:
    """
    python class for user credentials
    """
    credentials = {
        "license": "",
        "client_id": "BNT5xP3mtVS0zfzU5gWGdcSN8f4RstEnvZPyoHUp",
        "client_secret": "cnMe6DTjgKLBR1UAtHquYKMEnLHY7WG5KJfZCB5zFf3UhTOfbFKbalIBMl3OOgoNmfQpvW03n8KfGkafUyjo154PyyCsXOXnt5hec0U95dLsd4ej85rGOijFgATzT4p1",
        "debit": 100
    }

    def __init__(self, screen_width=1024, screen_height=768):
        self.screen_width = screen_width
        self.screen_height = screen_height
