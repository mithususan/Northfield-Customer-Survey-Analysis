"""
Synthetic data for a fictional insurer/bank ("Northfield Financial"), minimal version.
Simulates RAW EXTRACTS from three source systems as four pipe-delimited files in ./data:

  survey_platform.invitation / response   survey platform (Medallia/Qualtrics-style)
  contact_centre.interaction              contact-centre platform (calls and emails)
  crm.customer                            customer table with start/end (churn) dates

All data is SYNTHETIC. Planted so the analysis has signal:
  1. From 1 Mar to 30 Jun 2026 phone queues get longer, first-contact resolution
     drops and billing contacts rise, so phone NPS falls, then partly recovers.
  2. Phone survey response rate collapses 2 Mar - 26 Apr 2026 (survey hand-off change).
  3. Detractors churn at roughly 3x the rate of promoters.
Realistic imperfections: ~25% of surveys carry no customer reference (phone/email
can still be linked through interaction_id), the contact centre calls phone 'Voice',
messy channel labels, duplicate import batch, missing and invalid scores.

Run:  python generate_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(11)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

START, END = pd.Timestamp("2025-10-01"), pd.Timestamp("2026-09-20")
NDAYS = (END - START).days + 1
N_CUST, N_SENT, N_EXTRA_INT = 8_000, 20_000, 8_000
PRODUCTS = ["Auto Insurance", "Home Insurance", "Credit Card", "Mortgage"]
REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Web", "App", "Phone", "Branch", "Email"]


def day_no(ts):
    x = pd.to_datetime(ts) - START
    return x.dt.days if isinstance(x, pd.Series) else x.days


def write(df, name):
    for c in df.columns:
        if df[c].dtype == object:
            assert not df[c].astype(str).str.contains(r"\||\"").any(), f"{name}.{c} has delimiter/quote"
    df.to_csv(OUT / f"{name}.txt", sep="|", index=False, lineterminator="\n", quoting=3)
    print(f"  {name}.txt: {len(df):,} rows")


# ------------------------------------------------------------- daily conditions
t = np.arange(NDAYS)
bad = (t >= day_no("2026-03-01")) & (t <= day_no("2026-06-30"))          # service-pressure window
queue = 240 + rng.normal(0, 20, NDAYS) + 260 * bad                        # avg phone queue (s)
p_fcr_ph = np.where(bad, 0.55, 0.80)
p_billing = np.where(bad, 0.40, 0.15)

# -------------------------------------------------------------------- customers
c_product = rng.choice(PRODUCTS, N_CUST, p=[0.30, 0.25, 0.25, 0.20])
c_region = rng.choice(REGIONS, N_CUST)
c_tier = rng.choice(["Standard", "Silver", "Gold"], N_CUST, p=[0.60, 0.28, 0.12])
c_start = pd.Timestamp("2012-01-01") + pd.to_timedelta(
    rng.integers(0, (pd.Timestamp("2025-09-30") - pd.Timestamp("2012-01-01")).days, N_CUST), unit="D")

# ------------------------------------------------------------------ invitations
sent = pd.DataFrame({
    "sent_date": START + pd.to_timedelta(rng.integers(0, NDAYS, N_SENT), unit="D"),
    "cust_idx": rng.integers(0, N_CUST, N_SENT),
    "channel": rng.choice(CHANNELS, N_SENT, p=[0.24, 0.24, 0.28, 0.12, 0.12]),
}).sort_values("sent_date", kind="stable").reset_index(drop=True)
sent["survey_id"] = [f"S{i:06d}" for i in range(1, N_SENT + 1)]
ci, ch = sent["cust_idx"].to_numpy(), sent["channel"].to_numpy()
d = day_no(sent["sent_date"]).to_numpy()
product, region = c_product[ci], c_region[ci]

# ------------------------------------------------- interactions (phone and email)
OTHER = ["Claims", "Policy change", "Login help", "Payment", "General enquiry"]
TEAMS = [f"Team {c}" for c in "ABCDEF"]


def interaction_attrs(chan, di):
    n = len(chan)
    ph = chan == "Phone"
    wait = np.where(ph, rng.gamma(2.5, queue[di] / 2.5), rng.gamma(2, 7200)).round().astype(int)
    handle = np.where(ph, rng.gamma(3, 110), rng.gamma(2, 160)).round().astype(int)
    fcr = (rng.random(n) < np.where(ph, p_fcr_ph[di], 0.75)).astype(int)
    reason = np.where(rng.random(n) < p_billing[di], "Billing", rng.choice(OTHER, n))
    return wait, handle, fcr, rng.choice(TEAMS, n), reason


idx_int = np.where(np.isin(ch, ["Phone", "Email"]))[0]
n_int = len(idx_int)
d_int = np.maximum(d[idx_int] - rng.integers(0, 2, n_int), 0)
ch_int = ch[idx_int]
w_i, h_i, f_i, t_i, r_i = interaction_attrs(ch_int, d_int)
ch_x = rng.choice(["Phone", "Email"], N_EXTRA_INT, p=[0.7, 0.3])
d_x = rng.integers(0, NDAYS, N_EXTRA_INT)
w_x, h_x, f_x, t_x, r_x = interaction_attrs(ch_x, d_x)

ix = pd.DataFrame({
    "cust_idx": np.concatenate([ci[idx_int], rng.integers(0, N_CUST, N_EXTRA_INT)]),
    "day": np.concatenate([d_int, d_x]), "channel": np.concatenate([ch_int, ch_x]),
    "wait": np.concatenate([w_i, w_x]), "handle": np.concatenate([h_i, h_x]),
    "fcr": np.concatenate([f_i, f_x]), "team": np.concatenate([t_i, t_x]),
    "reason": np.concatenate([r_i, r_x]),
})
ix["ts"] = START + pd.to_timedelta(ix["day"], unit="D") + pd.to_timedelta(
    rng.integers(8 * 3600, 18 * 3600, len(ix)), unit="s")
order = np.argsort(ix["ts"].to_numpy(), kind="stable")
ids = np.empty(len(ix), dtype=object)
ids[order] = [f"I{k:07d}" for k in range(1, len(ix) + 1)]
ix["interaction_id"] = ids

# ------------------------------------------------------------------- NPS scores
mean = np.full(N_SENT, 7.1)
mean += pd.Series(ch).map({"Web": 0.0, "App": 0.1, "Phone": -0.2, "Branch": 0.5, "Email": -0.2}).to_numpy()
mean += pd.Series(product).map({"Auto Insurance": 0.0, "Home Insurance": 0.1, "Credit Card": -0.2,
                                "Mortgage": 0.2}).to_numpy()
mean += pd.Series(c_tier[ci]).map({"Standard": 0.0, "Silver": 0.2, "Gold": 0.5}).to_numpy()
ph = ch_int == "Phone"
adj = np.where(ph, -0.8 * np.log(np.maximum(w_i, 30) / 240), -0.3 * np.log(np.maximum(w_i, 600) / 14400))
adj += np.where(f_i == 1, 0.9, -1.2)
mean[idx_int] += adj
score = np.clip(np.rint(rng.normal(mean, 2.1)), 0, 10)
csat = np.clip(np.rint(score / 10 * 4 + 1 + rng.normal(0, 0.6, N_SENT)), 1, 5)

# --------------------------------------------------------------------- comments
NEG = {
    "billing": ["Billed twice this month and nobody could explain why.",
                "Premium amount on my statement doesn't match what I was quoted.",
                "Had to call three times to fix a billing error."],
    "wait": ["Waited far too long to speak to someone.",
             "Long hold time, then I was transferred and had to repeat myself."],
    "login": ["The app keeps logging me out.",
              "Couldn't log in after the update, had to reset my password twice.",
              "Login is painful, the app is slow."],
    "crash": ["The app crashed twice while I was paying.", "App froze when I tried to submit my claim."],
    "claims": ["My claim is taking much longer than promised.", "No updates on my claim unless I chase you."],
    "pricing": ["Renewal price went up with no explanation.", "Fees are higher than competitors."],
}
POS = ["Quick and easy, thanks.", "Staff were helpful and friendly.", "Problem solved first time.",
       "Great experience, very smooth.", "The new app is much easier to use.",
       "Clear communication throughout."]
NEU = ["It was fine.", "Nothing special, did the job.", "Okay overall."]
bad_day = bad[d]


def make_comment(i, s):
    if rng.random() > 0.6:
        return ""
    if s >= 9:
        return rng.choice(POS)
    if s >= 7:
        return rng.choice(NEU + POS[:2])
    if ch[i] == "Phone" and bad_day[i] and rng.random() < 0.6:
        theme = "billing" if rng.random() < 0.6 else "wait"
    else:
        theme = rng.choice(list(NEG))
    return rng.choice(NEG[theme])


# ---------------------------------------------------------------- who responds
p = pd.Series(ch).map({"Web": 0.22, "App": 0.30, "Phone": 0.20, "Branch": 0.25, "Email": 0.12}).to_numpy().copy()
p[(ch == "Phone") & sent["sent_date"].between("2026-03-02", "2026-04-26").to_numpy()] = 0.06
responded = rng.random(N_SENT) < p
ridx = np.where(responded)[0]
lag = np.minimum(rng.exponential(1.8, len(ridx)).astype(int), 7)
resp = pd.DataFrame({
    "survey_id": sent.loc[ridx, "survey_id"].values,
    "response_date": sent.loc[ridx, "sent_date"].values + pd.to_timedelta(lag, unit="D"),
    "nps_score": score[ridx], "csat": csat[ridx],
    "comment": [make_comment(i, score[i]) for i in ridx],
})
resp["nps_score"] = resp["nps_score"].astype("Float64")

# ---------------------------------------------------- planted data-quality issues
resp.loc[rng.random(len(resp)) < 0.015, "nps_score"] = pd.NA                          # missing scores
badv = rng.random(len(resp)) < 0.003
resp.loc[badv, "nps_score"] = rng.choice([-1, 11], badv.sum())                        # invalid scores
dup = resp[resp["response_date"].between("2026-05-18", "2026-05-20")]                 # duplicate batch
resp = pd.concat([resp, dup], ignore_index=True).sort_values(["response_date", "survey_id"]).reset_index(drop=True)
resp["response_date"] = pd.to_datetime(resp["response_date"]).dt.strftime("%Y-%m-%d")
resp["nps_score"] = resp["nps_score"].astype("Int64")
resp["csat"] = resp["csat"].astype("Int64")

# ------------------------------------------------ survey-platform identifiers
ref = np.where(rng.random(N_SENT) < 0.75, [f"C{x + 1:05d}" for x in ci], "")           # ~25% have no ref
iid = np.full(N_SENT, "", dtype=object)
iid[idx_int] = np.where(rng.random(n_int) < 0.85, ix["interaction_id"].to_numpy()[:n_int], "")
variants = {"Web": ["web", "WEB", "Web "], "App": ["app", "Mobile App"], "Phone": ["phone", "Telephone", "PHONE "],
            "Branch": ["branch", "Branch "], "Email": ["email", "E-mail"]}
ch_lbl = np.array([rng.choice(variants[c]) if m else c for c, m in zip(ch, rng.random(N_SENT) < 0.05)])
inv = pd.DataFrame({"survey_id": sent["survey_id"], "customer_ref": ref, "interaction_id": iid,
                    "sent_date": sent["sent_date"].dt.strftime("%Y-%m-%d"), "channel": ch_lbl,
                    "product": product, "region": region})

# ------------------------------------------------------------ churn (crm.customer)
worst = pd.Series(score[ridx]).groupby(ci[ridx]).min()
c_worst = np.full(N_CUST, np.nan)
c_worst[worst.index.to_numpy()] = worst.to_numpy()
last_inv = pd.DataFrame({"c": ci, "d": sent["sent_date"].values}).groupby("c")["d"].max().reindex(range(N_CUST))
base_date = last_inv.fillna(pd.Timestamp("2025-12-01")).to_numpy()
pc = np.where(np.isnan(c_worst), 0.10, np.where(c_worst >= 9, 0.09, np.where(c_worst >= 7, 0.16, 0.36)))
churn = rng.random(N_CUST) < pc
end_dt = pd.to_datetime(base_date) + pd.to_timedelta(rng.exponential(60, N_CUST).astype(int) + 7, unit="D")
end_rec = pd.to_datetime(pd.Series(np.where(churn & (end_dt <= END), end_dt, pd.NaT)))
rev = pd.Series(c_product).map({"Auto Insurance": 1500, "Home Insurance": 1800, "Credit Card": 320,
                                "Mortgage": 2600}).to_numpy()
cust = pd.DataFrame({
    "customer_id": [f"C{i:05d}" for i in range(1, N_CUST + 1)], "product": c_product, "region": c_region,
    "loyalty_tier": c_tier, "start_date": pd.Series(c_start).dt.strftime("%Y-%m-%d"),
    "end_date": end_rec.dt.strftime("%Y-%m-%d").fillna(""),
    "annual_revenue": (rev * rng.lognormal(0, 0.25, N_CUST)).round(2),
})

# ------------------------------------------------------------- interaction output
ixo = ix.sort_values("ts").assign(
    customer_id=lambda x: [f"C{i + 1:05d}" for i in x["cust_idx"]],
    interaction_ts=lambda x: x["ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    channel=lambda x: np.where(x["channel"] == "Phone", "Voice", "Email"),
    queue_wait_seconds=lambda x: x["wait"], handle_seconds=lambda x: x["handle"],
    first_contact_resolved=lambda x: x["fcr"], agent_team=lambda x: x["team"], reason_code=lambda x: x["reason"],
)[["interaction_id", "customer_id", "interaction_ts", "channel", "queue_wait_seconds", "handle_seconds",
   "first_contact_resolved", "agent_team", "reason_code"]]

print("Writing raw extracts:")
write(inv, "invitation")
write(resp[["survey_id", "response_date", "nps_score", "csat", "comment"]], "response")
write(ixo, "interaction")
write(cust, "customer")
