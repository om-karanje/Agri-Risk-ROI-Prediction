# Phase 2 --- Data Acquisition & Preprocessing (ETL Pipeline)

## AgriRisk and ROI Prediction

This phase prepares the agricultural dataset for downstream
machine-learning model training.

The objective of Phase 2 is to integrate crop-yield, soil, and climate
information at district/year level, construct a leakage-safe historical
yield baseline, convert yield into the financial unit required by the
project, attach official MSP/FRP values, calculate actual and target
revenue, and generate a validated supervised-learning dataset.

------------------------------------------------------------------------

## 1. Phase 2 Objective

The Phase 2 ETL pipeline transforms the raw agricultural data into a
clean, complete, auditable dataset suitable for ML modelling.

The pipeline performs:

1.  Crop-yield data preparation
2.  Soil-texture integration
3.  District-level climate integration
4.  Environmental missing-value completion
5.  Soil-composition correction for imputed records
6.  Historical 10-year district baseline construction
7.  Yield conversion from kg/ha to quintal/acre
8.  MSP/FRP mapping
9.  Actual revenue calculation
10. Historical target revenue calculation
11. Binary financial success-label creation
12. Final ML dataset preparation and quality validation

------------------------------------------------------------------------

## 2. Source Data

### Crop Yield

The master crop-yield dataset contains district-level observations for:

-   12 crops
-   Agricultural years 2013-14 through 2024-25
-   State and district information
-   Area
-   Production
-   Yield

The internal year representation uses the starting agricultural year:

-   2013-14 → 2013
-   2014-15 → 2014
-   ...
-   2024-25 → 2024

Therefore, the supervised labelled dataset covers 2014--2024 because a
historical baseline cannot be constructed for the first year.

### Soil

Soil information is derived from the NRSC/Bhuvan Indian Soil Dataset at
5 km × 5 km resolution.

The soil texture parameters used are:

-   Clayey fraction
-   Clayey skeletal fraction
-   Loamy fraction
-   Sandy fraction

Soil type is derived from the available texture information.

District boundaries are used for district-level spatial aggregation.

### Climate

Climate information is obtained from NASA POWER monthly data and
aggregated into annual and monsoon-period district-level indicators.

The climate variables include:

-   Rainfall
-   Mean temperature
-   Maximum temperature
-   Minimum temperature
-   Relative humidity
-   Wind speed
-   Solar radiation

------------------------------------------------------------------------

## 3. Phase 2 Notebook Pipeline

  Notebook   Purpose
  ---------- ----------------------------------------
  10         Soil texture processing
  11         Climate / NASA POWER processing
  12         Crop + soil + climate integration
  13         Environmental completion
  13.1       Soil imputation/composition correction
  14         Historical 10-year district baseline
  15         MSP/FRP, revenue and success label
  16         Final ML modelling dataset preparation

The notebooks are retained in the repository as the reproducibility
record for Phase 2.

------------------------------------------------------------------------

# 4. Environmental Integration

The crop, soil and climate datasets were integrated using
state/district/year-aware keys wherever applicable.

A key principle of the integration is that soil and climate information
is not merged using district name alone when a state-aware mapping is
available.

The completed environmental dataset preserves all original crop records.

### Final integrated row count

**67,826 rows**

No original crop-yield records were intentionally deleted during
environmental completion.

------------------------------------------------------------------------

# 5. Environmental Missing-Value Handling

Some district/year combinations did not have directly observed
environmental information.

These records were retained rather than deleted.

### Climate completion

Remaining missing climate values were completed using:

1.  State + year median
2.  Year median
3.  Global median

### Soil completion

Remaining soil texture values were completed using:

1.  State-level reference texture distribution
2.  Normalized national reference when a state-level reference was
    unavailable

### Important soil correction

Independent median imputation of each soil fraction can produce a
texture vector whose components do not form a valid composition.

Therefore, for soil-imputed rows, the reference texture vector was
normalized so that:

``` text
clayey_fraction
+ clayey_skeletal_fraction
+ loamy_fraction
+ sandy_fraction
= 1
```

Observed/recovered soil values were preserved and were not overwritten.

Legitimate source zeros were also preserved.

------------------------------------------------------------------------

# 6. Data Provenance

Environmental provenance is retained through:

-   `soil_data_status`
-   `climate_data_status`
-   `environmental_data_status`

These fields indicate whether environmental values were
observed/recovered or required imputation.

They are retained primarily for auditing and reliability analysis.

They should not automatically be used as ML predictors.

------------------------------------------------------------------------

# 7. Historical 10-Year Baseline

A leakage-safe historical baseline was constructed using:

``` text
State + District + Crop + Soil Type
```

For every agricultural year, the baseline uses only historical
observations from previous years.

The current year's yield is excluded.

The baseline stores:

-   `historical_10yr_baseline_yield_kg_ha`
-   `historical_baseline_year_count`
-   `historical_baseline_start_year`
-   `historical_baseline_end_year`
-   `historical_baseline_yield_q_acre`

A maximum of the previous 10 agricultural years is used.

Missing historical yield values are ignored when calculating the mean.

### Important

A valid historical baseline is not available for all 2013 observations.
These observations are therefore retained but remain unlabelled for
supervised learning.

------------------------------------------------------------------------

# 8. Yield Unit Standardization

Yield is converted from:

``` text
kg/ha
```

to:

``` text
quintal/acre
```

using:

``` text
1 hectare = 2.47105381 acres
1 quintal = 100 kg
```

Therefore:

``` text
yield_q_acre = yield_kg_ha × 2.47105381 / 100
```

This conversion is used consistently for financial calculations.

------------------------------------------------------------------------

# 9. MSP / FRP Mapping

Official support-price values are mapped by:

``` text
Crop + Agricultural Year
```

For most crops, the support price is MSP.

Sugarcane uses the official **Fair and Remunerative Price (FRP)** rather
than MSP.

The dataset therefore contains:

``` text
support_price_rs_per_quintal
support_price_type
```

where:

``` text
Sugarcane → FRP
All other project crops → MSP
```

Support-price coverage is complete for the crop/year combinations used
in the project.

------------------------------------------------------------------------

# 10. Revenue and Target Formulation

### Actual Revenue

Actual revenue per acre is calculated as:

``` text
Actual Revenue
= Actual Yield (Q/acre)
× MSP/FRP (₹/Q)
```

### Target Revenue

The historical target is calculated as:

``` text
Target Revenue
= Historical Baseline Yield (Q/acre)
× MSP/FRP (₹/Q)
```

### Revenue Ratio

The dataset also contains:

``` text
revenue_vs_target_ratio
```

defined as:

``` text
Actual Revenue / Target Revenue
```

This variable is retained for analysis but must NOT be used as an input
feature for the supervised ML classifier because it directly contains
target/outcome information.

------------------------------------------------------------------------

# 11. Success Label

The project's binary target is:

``` text
success_label
```

Definition:

``` text
1 → Actual Revenue >= Target Revenue
0 → Actual Revenue < Target Revenue
```

Rows for which the actual yield or historical target cannot legitimately
be calculated are retained but remain unlabelled.

No artificial labels are created.

------------------------------------------------------------------------

# 12. Final Dataset Statistics

The complete Phase 2 financial dataset contains:

**67,826 rows**

The supervised-learning portion contains:

**58,185 labelled rows**

The retained unlabelled portion contains:

**9,641 rows**

### Label distribution

``` text
success_label = 0 → 22,307
success_label = 1 → 35,878
```

Approximate success rate among labelled observations:

**61.66%**

The class distribution is moderately imbalanced but not extreme.

------------------------------------------------------------------------

# 13. Final ML Split

The labelled data is divided chronologically:

  Split        Years            Rows
  ------------ ------------ --------
  Training     2014--2022     47,345
  Validation   2023            5,611
  Test         2024            5,229
  Total        2014--2024     58,185

This chronological design is intentional.

It allows the ML team to evaluate whether models trained on historical
agricultural years generalize to later years.

The 2024 test set must remain untouched until final model selection is
complete.

------------------------------------------------------------------------

# 14. ML Feature Set

The final handoff provides 32 candidate modelling features.

## Categorical Features

-   `state`
-   `district`
-   `crop`
-   `season`
-   `soil_type`
-   `support_price_type`

## Numerical Features

-   `year`
-   `area_ha`
-   `historical_10yr_baseline_yield_kg_ha`
-   `historical_baseline_year_count`
-   `historical_baseline_start_year`
-   `historical_baseline_end_year`
-   `historical_baseline_yield_q_acre`
-   `support_price_rs_per_quintal`
-   `clayey_fraction`
-   `clayey_skeletal_fraction`
-   `loamy_fraction`
-   `sandy_fraction`
-   `annual_rainfall_mm`
-   `annual_mean_temp_c`
-   `annual_max_temp_c`
-   `annual_min_temp_c`
-   `annual_relative_humidity_pct`
-   `annual_wind_speed_m_s`
-   `annual_solar_radiation`
-   `monsoon_rainfall_mm`
-   `monsoon_mean_temp_c`
-   `monsoon_max_temp_c`
-   `monsoon_min_temp_c`
-   `monsoon_relative_humidity_pct`
-   `monsoon_wind_speed_m_s`
-   `monsoon_solar_radiation`

Target:

``` text
success_label
```

------------------------------------------------------------------------

# 15. Features Explicitly Excluded to Prevent Leakage

The following outcome-derived fields must not be used as model inputs:

-   `yield_kg_ha`
-   `yield_q_acre`
-   `production_tonnes`
-   `actual_revenue_rs_per_acre`
-   `target_revenue_rs_per_acre`
-   `revenue_vs_target_ratio`
-   `yield_vs_historical_baseline_ratio`
-   `success_label`

These variables either directly determine the target or contain
information that would not be available as an independent predictor at
prediction time.

------------------------------------------------------------------------

# 16. Constant Feature

The current dataset contains only one unique value for:

``` text
season
```

The value is:

``` text
Annual
```

Therefore, the ML team should drop `season` from the actual modelling
matrix unless future data introduces meaningful seasonal variation.

This does not indicate a data-processing error.

------------------------------------------------------------------------

# 17. Irrigation Data

`irrigation_type` is not present in the current source data.

It has intentionally **not** been fabricated.

The current dataset should therefore not contain an invented:

``` text
Irrigated / Rainfed
```

classification.

If reliable irrigation data becomes available later, it can be
integrated as a separate enhancement.

------------------------------------------------------------------------

# 18. Quality Checks Completed

Phase 2 includes validation for:

-   Expected row count
-   Agricultural-year coverage
-   Crop coverage
-   Duplicate core records
-   Environmental completeness
-   Soil fraction bounds
-   Soil composition validity for imputed records
-   Non-negative physical quantities
-   Historical baseline leakage
-   MSP/FRP consistency
-   Support-price coverage
-   Label validity
-   Train/validation/test separation
-   Feature completeness
-   Leakage exclusion

Final model-ready labelled data has:

``` text
58,185 rows
0 missing selected model-feature cells
0 duplicate core records
binary success_label
```

------------------------------------------------------------------------

# 19. Important Modelling Rules

The ML team should follow these rules:

1.  Use the predefined chronological train/validation/test datasets.
2.  Do not randomly split the complete dataset as the primary evaluation
    strategy.
3.  Fit encoders, scalers and other preprocessing steps using training
    data only.
4.  Do not use the 2024 test set for hyperparameter tuning.
5.  Do not use outcome-derived variables as input features.
6.  Drop `season` because it is currently constant.
7.  Keep environmental provenance columns for auditing, but do not use
    them as predictors initially.
8.  Do not fabricate irrigation information.
9.  Do not blindly delete statistical outliers.
10. Report precision, recall, F1-score, ROC-AUC and PR-AUC in addition
    to accuracy.
11. Analyse performance separately by crop and, where sample sizes
    permit, by state/district.
12. Investigate model behaviour on observed/recovered versus imputed
    environmental records.
13. Perform explainability analysis, preferably using SHAP for the final
    tree/boosting model.
14. Keep the original Phase 2 handoff datasets unchanged.

------------------------------------------------------------------------

# 20. Recommended ML Workflow

The next phase should follow this sequence:

``` text
Final Phase 2 Dataset
        ↓
EDA
        ↓
Training-only preprocessing pipeline
        ↓
Baseline models
        ↓
Tree / ensemble models
        ↓
Validation comparison
        ↓
Hyperparameter tuning
        ↓
Feature importance
        ↓
SHAP explainability
        ↓
Crop/state performance analysis
        ↓
Probability calibration
        ↓
Final model selection
        ↓
One-time evaluation on 2024 test set
        ↓
Risk score generation
        ↓
Scenario / what-if analysis
```

------------------------------------------------------------------------

# 21. Phase 2 Handoff Files

The recommended ML handoff package is:

``` text
ML_TEAM_HANDOFF/
│
├── model_train_2013_2022.csv
├── model_validation_2023.csv
├── model_test_2024.csv
├── model_ready_labeled_2013_2025.csv
├── model_unlabeled_2013_2025.csv
├── model_feature_dictionary.csv
├── modeling_quality_audit.csv
└── FINAL_MODEL_DATASET_HANDOFF.txt
```

### Primary files

``` text
model_train_2013_2022.csv
model_validation_2023.csv
model_test_2024.csv
```

### Master supervised dataset

``` text
model_ready_labeled_2013_2025.csv
```

### Unlabelled records

``` text
model_unlabeled_2013_2025.csv
```

### Documentation and audit

``` text
model_feature_dictionary.csv
modeling_quality_audit.csv
FINAL_MODEL_DATASET_HANDOFF.txt
```

------------------------------------------------------------------------

# 22. Reproducibility

The Phase 2 notebooks should be retained in the repository because they
document the complete ETL process:

``` text
10_Soil_Texture_Processing.ipynb
11_Climate_Weather_Processing_fixed.ipynb
12_Crop_Soil_Climate_Integration_FINAL.ipynb
13_Complete_Crop_Soil_Climate_Dataset.ipynb
13_1_Soil_Imputation_Correction_REVISED.ipynb
14_Historical_10_Year_District_Baseline.ipynb
15_MSP_Revenue_Target_Success_Label.ipynb
16_Final_ML_Modeling_Dataset_Preparation.ipynb
```

The generated CSV handoff files should be treated as the outputs of this
pipeline.

------------------------------------------------------------------------

# 23. Phase 2 Completion Status

**Phase 2 --- Data Acquisition & Preprocessing: COMPLETED**

The dataset has been:

-   integrated
-   environmentally completed
-   corrected for soil-composition consistency
-   baseline-enhanced
-   financially labelled
-   leakage-audited
-   split chronologically
-   checked for missing model features
-   checked for duplicate core records
-   prepared for ML handoff

### Final supervised dataset

**58,185 labelled observations**

### Final chronological split

**47,345 train / 5,611 validation / 5,229 test**

### Remaining unlabelled observations

**9,641**

The project is now ready to proceed to the **Machine Learning Modelling
Phase**.
