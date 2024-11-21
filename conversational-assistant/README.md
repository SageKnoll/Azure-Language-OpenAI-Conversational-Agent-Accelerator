# Conversational Assistant

This project provides users with a code-first example on how to augment chat solutions with Azure AI Language functionality. 

### Context:
Azure AI Language offers two services: [Conversational Language Understanding](https://learn.microsoft.com/en-us/azure/ai-services/language-service/conversational-language-understanding/overview) (`CLU`) and [Custom Question Answering](https://learn.microsoft.com/en-us/azure/ai-services/language-service/question-answering/overview) (`CQA`). `CLU` analyzes user input to extract intents and entities. `CQA` uses pre-defined question-answer pairs or a pre-configured knowledge base to answer user questions. 

### Solution:
This project includes a `UnifiedConversationOrchestrator` class that unifies both `CLU` and `CQA` functionality. Using a variety of different routing strategies, the orchestrator can intelligently route user input to either `CLU` or `CQA` runtimes. There is also fallback functionality when any of the following occurs: neither runtime is called, API call failed, confidence threshold not met, `CLU` did not recognize an intent, `CQA` failed to answer the question. This fallback functionality can be configured to be any function. The orchestrator object takes a string message as input, and outputs a dictionary object containing information regarding what runtime was called, relevant outputs, was fallback called, etc.

### Benefits:
When combined with an existing `RAG` solution, adding a `UnifiedConversationOrchestrator` can help in the following ways:
-	Manual overrides of DSAT examples using `CQA`.
-	Extended chat functionality based on recognized intents/entities using `CLU`.
-	Consistent fallback to original chat functionality with `RAG`.

Further, users can provide their own business logic to call based on `CLU` results (e.g. with an `OrderStatus` intent and `OrderId` entity, users can include business logic to query their database to check the order status).

### Example Data:
This project includes sample data to create project dependencies. Sample data is in the context of a fictionary outdoor product company: Contoso Outdoors.

### Demo Experience:
The demo included with this project showcases the following chat experience:
-	User inputs chat.
-	Orchestrator routes input to either `CLU`, `CQA`, or fallback function.
-	If input was routed to `CLU`, call extended business logic based on recognized intent/entities.
-	Summarize routed response (what business action was performed, provide answer to question, fallback response).

### Prerequisites:
Users must have an [Azure AI Language resource](https://learn.microsoft.com/en-us/azure/ai-services/language-service/overview). 

1. Create/activate a new Python/Conda environment.
2. Install requirements: `pip install -r requirement.txt`
3. Copy the contents of `.env_schema.txt` into a new file name `.env`.
4. Follow the notebooks in `/setup/*.ipynb` to setup relevant project dependencies and populate your `.env` file.
5. Ensure all variables in `.env` are populated with values.

### Run the Demo:
```
python demo.py
```

### Architecture:
![architecture-diagram ](architecture.png)

### Routing Strategies:
- `BYPASS`: No routing. Only call fallback function.
- `CLU`: Route to CLU runtime only.
- `CQA`: Route to CQA runtime only.
- `ORCHESTRATION`: Route to either CQA or CLU runtime using an Azure AI Language [Orchestration](https://learn.microsoft.com/en-us/azure/ai-services/language-service/orchestration-workflow/overview) project to decide. 

In any case, the fallback function is called if routing "failed". `CLU` route is considered "failed" is confidence threshold is not met or no intent is recognized. `CQA` route is considered "failed" if confidence threhsold is not met or no answer is found. `ORCHESTRATION` and `FUNCTION_CALLING` routes depend on the return value of the runtime they call.

### Planned Updates:
- Add minimal demo chat UI.
- Integrate LLMs in demo/routing experience.

### Third-Party Dependencies:
This projects makes use of the following third-party OSS Python packages:
- [requests](https://pypi.org/project/requests/)
- [azure-ai-textanalytics](https://pypi.org/project/azure-ai-textanalytics/)
- [azure-identity](https://pypi.org/project/azure-identity/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)