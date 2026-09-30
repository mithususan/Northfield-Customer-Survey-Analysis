# northfield-Customer-Survey-Analysis
Power BI dashboard showing how satisfied customers are and where satisfaction is strongest or weakest, built from cleaned, multi-source survey data (synthetic).
# Customer Satisfaction Dashboard: A Voice of Customer Project

I took customer survey data from three different systems, cleaned and connected it, and built a Power BI dashboard
that shows how satisfied customers are and where satisfaction is strongest or weakest.

> **The data is artificial.** northfield Financial is a fictional bank and insurer, and all the data was generated for this
> project. It shows how I approach the work, not real business results.

Overview page:
<img width="1436" height="807" alt="dashboard1" src="https://github.com/user-attachments/assets/29505ff1-7e8f-4235-8ed8-1fd1eca629f6" />

Semantic model:
<img width="1030" height="731" alt="semanticmodeldgm" src="https://github.com/user-attachments/assets/46141cde-9085-45e2-8ca5-5792f4957c61" />


## The question

After customers contact a company, they are often asked "How likely are you to recommend us?" on a 0 to 10 scale.
The answers become the **Net Promoter Score (NPS)**:

- **Promoters** (9 to 10) are happy. **Passives** (7 to 8) are neutral. **Detractors** (0 to 6) are unhappy.
- **NPS = % promoters minus % detractors.** It runs from -100 to +100, and higher is better.

The dashboard answers: **How satisfied are our customers, and where is it strongest or weakest?**

## The dashboard

A two-page Power BI report (`VoC_NPS_northfield.pbix`).

- **Overview:** the headline numbers (NPS, average satisfaction score, survey invitations, responses and response
  rate), NPS by month, the mix of promoters, passives and detractors each month, invitations and responses by channel,
  and the response rate over time. Product tiles and channel and loyalty-tier buttons narrow the whole page.
- **Segments:** satisfaction compared across channel (phone, web, app, email, branch), product, region and customer
  loyalty level.

## What it shows

| | |
|---|---|
| Overall | NPS of **-3**, from about 4,300 survey answers. The average satisfaction score is 3.86 out of 5 |
| Response rate | **22%** of 20,000 survey invitations were answered. It dipped to about 19% in March and April 2026 |
| Over time | Monthly NPS stayed between about +3 and -9, and was lowest from March to June 2026 |
| By channel | **Branch** scores best (+15) and **Web** worst (-12) |

Possible next steps: find out why Web scores so much lower than Branch, and look into what happened in spring 2026
when both NPS and the response rate fell.

## How I built it

I used **AI assistance throughout** to learn unfamiliar tools and deliver faster than I could have alone. I worked with
**Claude**, an AI assistant, which I connected directly to my files and to my Power BI model through **MCP connectors**.
That let it read the project, help me build and check the work, and add and test calculations in the Power BI model.

1. **Data:** three sources (a survey platform, a call and email system, and a customer database), generated as sample
   data so no real customer information was used.
2. **Cleaning:** duplicate answers removed, invalid scores set aside, inconsistent channel names (such as "Phone",
   "PHONE" and "Telephone") unified, and surveys matched to customers across systems. Every removed or changed answer
   is logged with a reason.
3. **Dashboard:** satisfaction calculated and presented so anyone can use it without knowing the details.
4. **Checking:** I compared the dashboard's numbers against the values expected from the Power BI model.

Tools: SQL Server, Power BI, and Claude with MCP connectors.

## Things to keep in mind

- The data is synthetic, so the findings are illustrative.
- Some months have small samples (for example 29 and 34 phone answers in March and April), so read those with care.
- About 84% of survey invitations could be matched to a customer.

## Folder guide

| Item | What it is |
|---|---|
| `VoC_NPS_northfield.pbix` | The Power BI report |
| `data/` | The made-up source data |
| `generate_data.py` | The script that creates the data |
