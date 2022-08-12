# DI-team-tracker

An extremely extra way to track DI team metrics based on the DI surveys:
[Link to weekly survey](https://forms.office.com/Pages/DesignPageV2.aspx?origin=NeoPortalPage&subpage=design&id=VMQEKxY4FESUTTf_kH9z0d5wsWds7_REoQcg4UZEhv5UQUpVMk1NMUcxUjRBUDkxUE5HRENVQ1dONC4u&analysis=true)

[Link to monthly survey](https://forms.office.com/Pages/DesignPageV2.aspx?origin=NeoPortalPage&subpage=design&id=VMQEKxY4FESUTTf_kH9z0d5wsWds7_REoQcg4UZEhv5UQlRRR1RYUU9ZVjFSMU5HSUVTQTUwRDg1Qi4u&analysis=true)

To run the code:

1. Clone the repo
2. Download the most recent survey results (all history) and paste into src/data/Results in either Weekly or Monthly
3. In terminal, navigate to the project folder
4. Run `pipenv run python src/weekly.py` or `pipenv run python src/wmekly.py` to launch the dashboard
5. Run `pipenv run python src/send_email.py` to email Will and Hansa with the names of people who want to discuss their workload
