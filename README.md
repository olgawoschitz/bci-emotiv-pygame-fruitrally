#**Pygame memory shopping list.**

This is a simple memory game that works with keyboard and with BCI (Emotiv). All the player have to  do is to remember
the shopping list and recall it during the game in a correct order by putting the items into the shopping card.
The player will have only 5 seconds to memorize the shopping list. If the player caught the right item, he’ll hear a signal 
and see the item on the screen right, but if the player caught a wrong item, he will receive 5 seconds additionally to 
his score time. The goal is to catch all items on your list as fast as possible.


##**How to run this project**

To run this project it is recommended to setup a virtual environment by using requirements.txt file.

1.  `python3 -m venv .venv`
2.  `source .venv/bin/activate`
3.  `pip install -r requirements.txt`

4. For using BCI(Emotiv) add your user credentials into _user_credentials.py_ under 

        `"client_id": "<your id>",
        
        "client_secret": "<your secret>"`
        
   _if you don't know your credentials visit https://www.emotiv.com/my-account/cortex-apps/ and/or register a new application._

5. run the game: 

    `python game.py`


##**Credits**

Sounds:

- fail-buzzer.wav and 
- magic-chime.wav were taken from https://www.soundjay.com/. Copyright provides free use https://www.soundjay.com/tos.html
- GameSong.wav created by Olga Zharikova

Images: 

- all figure images were taken from https://www.freepikcompany.com under Copyright © 2010-2021 Freepik Company S.L.
- backgrounds and menu pictures created by Olga Zharikova 

Fonts:

- verdana.ttf - Copyright © Microsoft Corporation. Designer: Matthew Carter

