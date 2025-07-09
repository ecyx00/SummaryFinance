-- Table: economic_events
-- Purpose: Store economic calendar events from FMP API
-- Description: This table stores macroeconomic events like GDP releases, interest rate decisions,
-- employment reports, etc. from the Financial Modeling Prep API.

CREATE TABLE economic_events (
    id BIGSERIAL NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_value NUMERIC,
    forecast_value NUMERIC,
    previous_value NUMERIC,
    impact VARCHAR(50),  -- 'Low', 'Medium', 'High'
    unit VARCHAR(50),    -- %, USD, etc.
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (event_name, country, event_time)
);

-- Create index for faster retrieval by date range
CREATE INDEX idx_economic_events_time ON economic_events (event_time);

-- Create index for faster retrieval by country
CREATE INDEX idx_economic_events_country ON economic_events (country);

-- Create index for faster retrieval by impact
CREATE INDEX idx_economic_events_impact ON economic_events (impact);

COMMENT ON TABLE economic_events IS 'Economic calendar events from Financial Modeling Prep API';
COMMENT ON COLUMN economic_events.event_name IS 'Name of the economic event';
COMMENT ON COLUMN economic_events.country IS 'Country or region the event relates to';
COMMENT ON COLUMN economic_events.event_time IS 'Date and time when the event occurs';
COMMENT ON COLUMN economic_events.actual_value IS 'Actual reported value';
COMMENT ON COLUMN economic_events.forecast_value IS 'Forecasted value before event';
COMMENT ON COLUMN economic_events.previous_value IS 'Previous period value';
COMMENT ON COLUMN economic_events.impact IS 'Impact level of the event (Low, Medium, High)';
COMMENT ON COLUMN economic_events.unit IS 'Unit of measurement for the values';
