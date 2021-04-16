# %% Import libs
import redbrick

# %% Setting API keys and server url
api_key = "X7WiKsCVl-QiIklppFvGkg0xEUi1WHlE0jK1-fInq1g"
url = "https://piljxrnf0h.execute-api.us-east-1.amazonaws.com/qa/graphql/"
redbrick.init(api_key=api_key, url=url)

# %% Testing LabelsetLoader
org_id = "1e734f01-7c7c-44f6-a7ca-c1e1ac564466"
label_set_name = "Labelset Demo"

label_set = redbrick.labelset.LabelsetLoader(
    org_id=org_id, label_set_name=label_set_name
)

# %%
# label_set.show_data()

# %%
label_set.export(format="redbrick")

# %%
