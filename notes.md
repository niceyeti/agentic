

Config risks:
* AI developers outright encourage unsafe practices like env var based
  credential injection.
* API keys are conceivably accessible to the agent, if it were to jailbreak to
  the app environment.


Supply risks:

* OpenAI's responses api: this api is the backbone of this implementation, but
  is not a standardized api and couples this app with OpenAI.


