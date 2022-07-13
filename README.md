# DI-team-tracker

An extremely extra way to track DI team metrics based on the DI weekly survey:
[Link to survey](https://forms.office.com/Pages/DesignPageV2.aspx?subpage=design&FormId=VMQEKxY4FESUTTf_kH9z0d5wsWds7_REoQcg4UZEhv5UQUpVMk1NMUcxUjRBUDkxUE5HRENVQ1dONC4u&Token=6d8391f52b284173b5d218b5b3e68838)

To run the code:

1. Clone the repo
2. Download the most recent survey results (all history) and paste into src/data/Results
3. In terminal, navigate to the project folder
4. Run `pipenv run python src/main.py` to launch the dashboard
5. Run `pipenv run python src/send_email.py` to email Will and Hansa with the names of people who want to discuss their workload
