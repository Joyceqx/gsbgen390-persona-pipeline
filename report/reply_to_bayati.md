**Subject:** Re: Phase 1A predictions

Hi Mohsen,

Thank you. This is really helpful guidance, and a lovely piece of analysis. I
reran the whole notebook on the same file and everything reproduces. I agree we
should switch to normalized MAE as the main metric.

I also ran the regression myself, to see how the Random policy compares with the
four models and to put raw accuracy and normalized MAE side by side. Two things
came out, both lining up with yours:

1. On both metrics, the Random policy is genuinely a strong choice. It sits at the
   top on accuracy and near the best on normalized error.

2. Statistically the models barely differ. Once I cluster the standard errors by
   respondent (each respondent shows up many times, and each call has two
   near-identical draws), no model is significantly better than Random on either
   metric. Only Qwen separates, and it is worse.

The one thing I would like to flag, because it is the place the models really do
differ and the metrics miss it, is a mode-collapse problem. The two
confidence-in-institutions items are the clearest case: CONFINAN (confidence in
banks) and CONLEGIS (confidence in Congress). On those, every model except Kimi
gives essentially the same answer to all 200 respondents. Here is the share of
respondents who got each model's single most common answer (1.00 means one answer
for everyone):

| Model    | CONFINAN | CONLEGIS |
|----------|:--------:|:--------:|
| Qwen     |   0.86   |   1.00   |
| DeepSeek |   0.98   |   0.71   |
| Llama    |   1.00   |   0.99   |
| Kimi     |   0.85   |   0.81   |

The metrics actually reward this, since collapsing to the middle code keeps the
error small, but the model is ignoring the persona there. That matters for Phase 1B,
where we read a feature's importance from how much the prediction moves. I do not
have a clean resolution, and I wanted to put it in front of you rather than settle
it myself.

On the routing idea: it reproduces exactly, a gain of about 0.02 on normalized
error with the interval excluding zero. I have kept it as a secondary result. One
wrinkle is that its learned policy routes the collapse-prone questions to the
collapsing models, so the same issue resurfaces.

I have written all of this up with the figures and the full tables in the report
draft, so please take a look there for the details. Mostly I wanted to share where
I have gotten, and get your read on how to weigh the collapse issue against the
"no model beats Random" result.

Best,
Joyce
