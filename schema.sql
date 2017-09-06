DROP TABLE IF EXISTS hist_prices;

CREATE TABLE hist_prices (
  snap_time timestamp,
  ticker VARCHAR(10),
  data_source VARCHAR(30),
  high DECIMAL,
  low DECIMAL,
  open DECIMAL,
  close DECIMAL,
  weighted_avg DECIMAL,
  base_volume DECIMAL,
  quote_volume DECIMAL
)
;
