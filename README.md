# LoadLens

The purpose of this app is to leverage capabilities of Open AI's LLM for the use of extracting the most important data from transport orders.

## Set up

First, clone the repository:<br><br>
`git clone https://github.com/gugucharm/LoadLens.git`

Enter the repository, download the dependencies and create an environmental variable OPENAI_API_KEY:<br><br>
`cd LoadLens`<br>
`pip install -r requirements.txt`<br>
`$env:OPENAI_API_KEY="yourapikey"`<br>

Before running the app, you also need to upload the transport order/document in PDF format to ./orders.
There is also order.json file that is going to modified upon successful response from Open AI.
After uploading the PDF file rename it to "order.pdf" and run the app.<br><br>
`python app.py`

You can send the request to the API directly from api_test.http file, which you can find in RestClient Endpoints folder.
However, it will only work in case you're using VS Code and you have REST Client extension installed (it is the preferred way).
Also, before sending the request, you need to change the path to the order file from:<br><br>
`C:/Users/user/Documents/LoadLens/orders/order.pdf`<br><br>
to whatever the exact location of the file is, just remember to use an ABSOLUTE path.

The request will send the prompt to Open API and it's response will be converted into a JSON format in the location mentioned before.

## Room for improvement
### Overall thoughts

The software can incorporate many different ways and ideas to tailor it's functionality to a specific use case, company or exact personel that might be using it.
Prompting to Open API with orders' or document data can save a lot of manual work time for variety of branches of companies and therefore I see this software as 
only a part or a fragment of a bigger AI solution full of agents that can communicate within itself and solve problems on its own.

### Improvements for now

As far as receiving a response from Open AI, there might be a need for filtering the data in specific fields. For example, in "NIP" value we might get
just a number or country's prefix and a number. At that point we need to ask ourselves whether we need a distinc field for a prefix of a country and the "NIP"
or they have to be together (but in that case not every order will have a prefix before the VAT number).

Secondly, the upload http request might be volatile depending on your environment. I found it difficult to find a proper http request making use of a path to the file.
The current one is not a first go-for approach and I just stuck with the one that worked for me. If you come across issues with it, it will most probably be the
path itself that causes trouble.

Lastly, I run the software after some time and issue of Open AI's agent came up. Before sending the request it started supposedly breaking the prompt into pieces
(and I'm not talking about chunking here!) and consulting them with Open AI one by one which resulted in an error in the and and multiple requests instead of one.
I'm assuming this was introduced in new versions of llama-index. The has been fixed, I'll keep an eye for that in the future in case it comes up again.
