# Building a Real-time Voice Interface with OpenAI: From Prototype to Open Source Toolkit

In November 2024, I've had the opportunity to participate in the OpenAI Builders Lab in Paris, where I was able to explore the potential of the Realtime API. I was amazed by how quickly I could build a prototype for a real-time web-based voice interface that uses function calls. 

The initial prototype was focused on a cooking guide where you could ask for a recipe or ask for instructions on how to prepare a certain dish. It was an amazing and inspiring experience to me because I've spent the last 10 years building a similar technology. And it just works.

To go further, as I explored the possibilities of this prototype, it became clear there were some challenges to overcome before it could become a deployable product. That's why I created an open-source toolkit to address those problems.

#### Challenges and Solutions

* **WebSockets not well suited for longform connections:** The official OpenAI Realtime API toolkit relies on WebSockets, which proved unstable for long-term sessions over HTTP.  The OpenAI team suggested using WebRTC bridges for better stability. The toolkit implements WebRTC with a LiveKit integration.

* **Dynamic UI:** I wanted a dynamic UI that could respond to user input in real-time. This meant connecting the function calls from the model to the front-end functions using remote procedure calls (RPC) over WebRTC. This brings the voice interface to life, allowing users to interact with different functions of the app seamlessly.

* **Architecture:**  A clear separation was needed between the web app's backend, the AI agent's backend, and the front-end.  The toolkit achieves a lightweight design that is modular, has few dependencies, and is easy to use.

* **Roles:** To quickly iterate on the user experience, you need to refine the prompts / instructions of the agent very frequently. That's implemented through an architecture where the 'roles' are separated from the code, and allows to add and modify them very quickly