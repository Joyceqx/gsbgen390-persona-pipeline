# GSS Variables to Download — Phase 1 (Path A*)

**Generated:** 2026-05-02
**Source:** Park v2 Table 3 (~120 items he evaluated against) + Phase 1 feature-pool needs
**Target dataset:** GSS 2022 cross-section (most recent fully-released year)

This list is the **superset** for Path A* — covers both the Path A sensitivity-check eval (~120 items) and the Path B feature pool. The download is once; the eval-set vs feature-pool split happens in code (audited via `gss_feature_taxonomy.json`).

**Total variables: ~155**. Some Park items may have been retired or renamed in GSS 2022 — that's OK, we'll detect missing variables in the loader and document them in pre-reg.

---

## Quick option — just download all of GSS 2022

If pre-picking 155 variables on GSS Data Explorer is annoying, the simpler path:

1. On https://gssdataexplorer.norc.org/ → **Browse Variables**
2. Filter by **Year = 2022**
3. Click **"Add all to cart"** at top of results
4. Add cases (Year = 2022)
5. Create extract → CSV + codebook

GSS 2022 has ~700 variables × ~3500 respondents → CSV is ~20MB, easy to handle. We subset in code.

**This is what I recommend for speed.** No risk of missing a variable. The pre-reg locks the analysis set, not the download set.

---

## Detailed option — paste-able variable list

If you prefer to pick variables (e.g., GSS DE complains about extract size), use the list below.

### Comma-separated (for bulk paste, if GSS DE Quick Cart supports it)

```
natspac, natenvir, natheal, natcity, natdrug, nateduc, natrace, natarms, nataid, natfare, natroad, natsoc, natmass, natpark, natchld, natsci, natenrgy, uswary, prayer, courts, grass, gunlaw, owngun, hunt1, cappun, tax, sexeduc, pillok, xmarsex, homosex, marhomo, polhitok, polabuse, polattak, pornlaw, divlaw, spanking, discaffw, discaffm, discaff, fehire, fechld, fepresch, fefam, fepol, reg16, mobile16, famdif16, incom16, dwelown16, paeduc, padeg, maeduc, madeg, mawrkgrw, marital, widowed, divorced, martype, posslq, wrkstat, evwork, wrkgovt, partfull, wksub1, wksup1, unemp, union1, joblose, jobfind, vetyears, conarmy, conbus, conclerg, coneduc, confed, confinan, conjudge, conlabor, conlegis, conmedic, conpress, consci, contv, happy, hapmar, satjob, speduc, spdeg, spwrksta, spjew, spfund, spkath, colath, libath, spkrac, colrac, librac, spkcom, colcom, libcom, spkhomo, colhomo, libhomo, class, satfin, finalter, finrela, race, racdif1, racdif2, racdif3, racdif4, wlthwhts, wlthblks, wlthhsps, racwork, letin1a, getahead, aged, parsol, kidssol, abdefect, abnomore, abhlth, abpoor, abrape, absingle, abany, letdie1, suicide1, suicide2, suicide3, suicide4, fair, helpful, trust, vote20, pres20, if20who, vote16, pres16, if16who, polviews, partyid, news, relig, jew, relig16, jew16, attend, pray, postlife, bible, reborn, savesoul, relpersn, sprtprsn, born, granborn, uscitzn, fucitzn, mnthsusa, educ, degree, income, hispanic, sex, age, region, dwelown, othlang, health, life, hrs1, tvhours, eqwlth, helppoor, helpsick, helpblk, helpnot, fund, anomia5, anomia6, anomia7, hompop
```

### Grouped by purpose (for understanding)

#### Park's eval-set candidates (Path A sensitivity)

Most overlap with the categories below — these are the items Park's Table 3 reports per-item normalized accuracy on. Listed here for traceability:

**National priorities (`nat*`)**: natspac, natenvir, natheal, natcity, natdrug, nateduc, natrace, natarms, nataid, natfare, natroad, natsoc, natmass, natpark, natchld, natsci, natenrgy

**Confidence battery (`con*`)**: conarmy, conbus, conclerg, coneduc, confed, confinan, conjudge, conlabor, conlegis, conmedic, conpress, consci, contv

**Free speech / civil liberties (`spk*` / `col*` / `lib*`)**: spkath, colath, libath, spkrac, colrac, librac, spkcom, colcom, libcom, spkhomo, colhomo, libhomo

**Abortion battery (`ab*`)**: abdefect, abnomore, abhlth, abpoor, abrape, absingle, abany

**Racial attitudes (`racdif*`, `wlth*`)**: racdif1, racdif2, racdif3, racdif4, wlthwhts, wlthblks, wlthhsps, racwork, letin1a

**Gender attitudes (`fe*`)**: fehire, fechld, fepresch, fefam, fepol

**End of life**: letdie1, suicide1, suicide2, suicide3, suicide4

**Social mobility / class**: getahead, aged, parsol, kidssol, class, satfin, finalter, finrela

**Police / civil rights**: polhitok, polabuse, polattak

**Other attitudes**: cappun, gunlaw, grass, owngun, hunt1, sexeduc, pillok, xmarsex, homosex, marhomo, pornlaw, discaff, discaffw, discaffm, divlaw, spanking, prayer, courts, uswary, tax, helppoor, eqwlth, helpsick, helpblk, helpnot

**Generalized trust triad**: fair, helpful, trust

#### Demographic (Phase 1 feature bin) — ~12 items

```
age, sex, race, hispanic, region, educ, degree, marital, wrkstat, income, hompop, born
```

#### Behavioral (Phase 1 feature bin) — ~10 items

```
vote20, vote16, attend, pray, news, hrs1, tvhours, partyid, relig, fund
```

(`vote16` and `vote20` both included — most recent presidential cycles. `relig` and `fund` are religious-affiliation behaviors. `partyid` is registered/expressed affiliation, treated as behavior here per the design doc.)

#### Psychological (Phase 1 feature bin) — GSS-thin, ~6 items

```
happy, satfin, life, health, anomia5, anomia6, anomia7
```

(Anomia items measure powerlessness / disposition. `happy` and `life` are dispositional vs attitudinal — a fuzzy boundary; locked as psychological for consistency with the pilot.)

#### Attitudinal feature pool (Phase 1 feature bin)

The largest category — every Park-eval item NOT in the curated 12-item primary eval (the latter is locked separately in `gss_feature_taxonomy.json` once we see actual data).

Tentatively, Path B's 12-item curated primary eval will be:
```
polviews   partyid   abany   cappun   gunlaw   fechld
fepol      racdif1   confinan  conlegis  helppoor  satfin
```

(One item per construct family to minimize within-eval auto-correlation.)

The remaining attitudinal items become the attitudinal feature bin — covers ~70 items including the rest of the abortion battery, free-speech battery, confidence battery, gender battery, etc.

---

## Codebook — also download

Make sure to **also download the codebook PDF** with the data extract. We need it for:
- Variable wordings (the actual question text the LLM persona will be asked to answer)
- Response value labels (so we can interpret 1/2/3/4 codes back to "very happy" / "pretty happy" / "not too happy")
- Time-of-asking notes (some items rotate across waves — verify availability in 2022)

---

## After you download

Drop the files in:
```
~/Documents/GSBGEN390/data/gss/
  GSS2022.csv         (or .dta if you prefer Stata)
  GSS2022_codebook.pdf
```

I'll create the folder when you're ready. Then I unblock and build the loader (task #5).
