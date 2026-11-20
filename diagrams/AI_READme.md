PawlPal+ app where you can schedule your pet so you can get a reminder to do the task just in case you forgot to do. its plain and easy to read on how to setup your pet. So right now i have implemented RAG system and guardrails To this app using google gemini API. so you can ask any type of question you wanna know about your specific pet. Also show a little animation on the top right corner of how long it takes for question to be finished by AI. so it can Answer the question. 

I also added a list of breeds of what type of pet you got. Just in case the Owner forgot whats the name of the breed and if they cant find it then there is a option where the owner can type the name of the breed. So my system diagram is pretty similar to the original project at the start.


How to setup or run my code. 
1. Download the folder/file to your local machine on my github. 
2. Clone my github
3. Get an Anthropic or Gemini API key. For the AI to work. 
4. run this in your terminal. python -m streamlit run app.py
5. The website should pop up
6. you can test any type of pet you want and then ask AI some questions about your pet or set up a schedule for your pet as well. 

AI output result:
1. 
Q: How often should an older cat see the vet?

Senior cats (10 years and older) should be examined every six months.

Source: General Guidance ([cats.md - Cat vet visits]).

2. 
: Add a 6pm walk for Casper every day

Add this to the schedule?

walk for Casper on Thu Nov 19 at 18:00 (30 min, repeats daily)



The reason why improve it more because A person wants as much information as possible for their dog and so do it as a owner who is worried about their pet and was wondering or wants a reminder what task i need to do because some of us are really busy and sometimes we forget to give our pet some attention in which they cant do for themself. Everything works. There is lots of improvements i want to build for this project so that people can easily understand whats going on and how easy and simple it is to setup everything for their pets. 

This project has taught me the way AI is very useful such as grabbing actual and precise data for the owner to grab information for their pets. and Add guardrails in case of any harmful things they might ask.And a RAG system so it would only focus on your pets instead of anywhere else. 