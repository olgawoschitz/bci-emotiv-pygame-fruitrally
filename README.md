# **Pygame memory shopping list.**

This is a simple memory game that works with a keyboard and with Cortex API (Emotiv). All you have to  do is to remember
the shopping list and recall it during the game in the correct order by putting the items into the shopping cart. The player will have only 5 seconds to memorize the shopping list. If you caught the right item, you’ll hear a signal and see the item on the screen right, but if you caught a wrong item, you will get 5 seconds additionally to your score time. The goal is to catch all items on your list as fast as possible. 

Since mental command training is quite complicated. You can have a strong signal for right-command and a weak signal for left-command, in the game you will get tested on your command power. Based on this score you will get specified minimal power of the signal for the move.


## **How to run this project**

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


## **Credits**

Sounds:

- fail-buzzer.wav and 
- magic-chime.wav were taken from https://www.soundjay.com/. Copyright provides free use https://www.soundjay.com/tos.html
- GameSong.wav created by Olga Zharikova

Images: 

- all figure images were taken from https://www.freepikcompany.com under Copyright © 2010-2021 Freepik Company S.L.
- backgrounds and menu pictures created by Olga Zharikova 

Fonts:

- verdana.ttf - Copyright © Microsoft Corporation. Designer: Matthew Carter

