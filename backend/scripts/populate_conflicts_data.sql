-- SQL script to populate test conflict data
-- Run this directly in your PostgreSQL database

-- Clear existing test data if needed
-- TRUNCATE articles CASCADE;
-- TRUNCATE events CASCADE;

-- Insert Gaza Conflict Event
INSERT INTO events (
    summary, articles_count, unique_sources, geo_diversity, evidence_flag,
    official_match, truth_score, confidence_tier, underreported, coherence_score,
    has_conflict, conflict_severity, conflict_explanation_json, bias_compass_json,
    category, category_confidence, importance_score, first_seen, last_seen, languages_json
) VALUES (
    'Gaza-Israel Conflict Escalates with New Violence',
    5, 5, 0.8, false, false, 65.0, 'developing', false, 72.5,
    true, 'medium', NULL, '{"left": 0.3, "center": 0.4, "right": 0.3}',
    'international', 0.95, 85.0, NOW(), NOW(), '["en"]'
) RETURNING id AS event_1_id;

-- Store event ID (you'll need to get this from the INSERT above)
-- For now, we'll use a CTE to capture it

WITH event_gaza AS (
    INSERT INTO events (
        summary, articles_count, unique_sources, geo_diversity, evidence_flag,
        official_match, truth_score, confidence_tier, underreported, coherence_score,
        has_conflict, conflict_severity, conflict_explanation_json, bias_compass_json,
        category, category_confidence, importance_score, first_seen, last_seen, languages_json
    ) VALUES (
        'Gaza-Israel Conflict Escalates with New Violence',
        5, 5, 0.8, false, false, 65.0, 'developing', false, 72.5,
        true, 'medium', NULL, '{"left": 0.3, "center": 0.4, "right": 0.3}',
        'international', 0.95, 85.0, NOW(), NOW(), '["en"]'
    ) RETURNING id
)
INSERT INTO articles (url, source, title, content, summary, published_at, ingested_at, authors, images, key_entities, cluster_id)
VALUES
    ('https://foxnews.com/article-gaza-1', 'foxnews.com', 'Hamas Attack Devastates Israeli Communities', 'Article about Gaza conflict from foxnews', 'Hamas Attack Devastates Israeli Communities', NOW() - INTERVAL '4 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_gaza)),
    ('https://cnn.com/article-gaza-1', 'cnn.com', 'Israel Responds to Attack; Civilian Casualties Reported', 'Article about Gaza conflict from cnn', 'Israel Responds to Attack; Civilian Casualties Reported', NOW() - INTERVAL '3 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_gaza)),
    ('https://aljazeera.com/article-gaza-1', 'aljazeera.com', 'Palestinian Resistance Operation Targets Military', 'Article about Gaza conflict from aljazeera', 'Palestinian Resistance Operation Targets Military', NOW() - INTERVAL '2 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_gaza)),
    ('https://bbc.com/article-gaza-1', 'bbc.com', 'Escalation in Gaza as Violence Intensifies', 'Article about Gaza conflict from bbc', 'Escalation in Gaza as Violence Intensifies', NOW() - INTERVAL '1 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_gaza)),
    ('https://npr.org/article-gaza-1', 'npr.org', 'Middle East Crisis as Conflict Spreads', 'Article about Gaza conflict from npr', 'Middle East Crisis as Conflict Spreads', NOW(), NOW(), '{}', '{}', '{}', (SELECT id FROM event_gaza));

-- Insert Trump Legal Case Event
WITH event_trump AS (
    INSERT INTO events (
        summary, articles_count, unique_sources, geo_diversity, evidence_flag,
        official_match, truth_score, confidence_tier, underreported, coherence_score,
        has_conflict, conflict_severity, conflict_explanation_json, bias_compass_json,
        category, category_confidence, importance_score, first_seen, last_seen, languages_json
    ) VALUES (
        'Trump Faces Indictment',
        5, 5, 0.2, false, true, 78.0, 'confirmed', false, 68.0,
        true, 'medium', NULL, '{"left": 0.5, "center": 0.3, "right": 0.2}',
        'politics', 0.98, 92.0, NOW(), NOW(), '["en"]'
    ) RETURNING id
)
INSERT INTO articles (url, source, title, content, summary, published_at, ingested_at, authors, images, key_entities, cluster_id)
VALUES
    ('https://foxnews.com/article-trump-1', 'foxnews.com', 'Trump Faces Politically Motivated Charges', 'Article from foxnews', 'Trump Faces Politically Motivated Charges', NOW() - INTERVAL '9 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_trump)),
    ('https://cnn.com/article-trump-1', 'cnn.com', 'Trump Indicted on Multiple Charges in Historic Case', 'Article from cnn', 'Trump Indicted on Multiple Charges in Historic Case', NOW() - INTERVAL '8 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_trump)),
    ('https://nytimes.com/article-trump-1', 'nytimes.com', 'Former President Charged in Federal Indictment', 'Article from nytimes', 'Former President Charged in Federal Indictment', NOW() - INTERVAL '7 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_trump)),
    ('https://washingtonpost.com/article-trump-1', 'washingtonpost.com', 'Trump Faces Serious Legal Jeopardy', 'Article from washingtonpost', 'Trump Faces Serious Legal Jeopardy', NOW() - INTERVAL '6 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_trump)),
    ('https://theguardian.com/article-trump-1', 'theguardian.com', 'Trump Charges Represent Unprecedented Legal Moment', 'Article from theguardian', 'Trump Charges Represent Unprecedented Legal Moment', NOW() - INTERVAL '5 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_trump));

-- Insert Border/Immigration Event
WITH event_border AS (
    INSERT INTO events (
        summary, articles_count, unique_sources, geo_diversity, evidence_flag,
        official_match, truth_score, confidence_tier, underreported, coherence_score,
        has_conflict, conflict_severity, conflict_explanation_json, bias_compass_json,
        category, category_confidence, importance_score, first_seen, last_seen, languages_json
    ) VALUES (
        'Border Crossing Numbers Reach New Levels',
        5, 5, 0.6, false, true, 72.0, 'developing', false, 75.0,
        true, 'low', NULL, '{"left": 0.3, "center": 0.4, "right": 0.3}',
        'politics', 0.92, 78.0, NOW(), NOW(), '["en"]'
    ) RETURNING id
)
INSERT INTO articles (url, source, title, content, summary, published_at, ingested_at, authors, images, key_entities, cluster_id)
VALUES
    ('https://foxnews.com/article-border-1', 'foxnews.com', 'Border Crisis: Surge of Illegal Crossings', 'Article from foxnews', 'Border Crisis: Surge of Illegal Crossings', NOW() - INTERVAL '14 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_border)),
    ('https://cnn.com/article-border-1', 'cnn.com', 'Biden Administration Addresses Border Challenges', 'Article from cnn', 'Biden Administration Addresses Border Challenges', NOW() - INTERVAL '13 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_border)),
    ('https://bbc.com/article-border-1', 'bbc.com', 'US Border Experiences Record Crossings', 'Article from bbc', 'US Border Experiences Record Crossings', NOW() - INTERVAL '12 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_border)),
    ('https://apnews.com/article-border-1', 'apnews.com', 'Border Crossings Reach New Levels', 'Article from apnews', 'Border Crossings Reach New Levels', NOW() - INTERVAL '11 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_border)),
    ('https://politico.com/article-border-1', 'politico.com', 'Immigration Becomes Central Political Issue', 'Article from politico', 'Immigration Becomes Central Political Issue', NOW() - INTERVAL '10 hours', NOW(), '{}', '{}', '{}', (SELECT id FROM event_border));

-- Verify data was created
SELECT 'Gaza Event' as event_name, COUNT(*) as article_count FROM articles WHERE source IN ('foxnews.com', 'cnn.com', 'aljazeera.com', 'bbc.com', 'npr.org')
UNION ALL
SELECT 'Trump Event', COUNT(*) FROM articles WHERE source IN ('foxnews.com', 'cnn.com', 'nytimes.com', 'washingtonpost.com', 'theguardian.com')
UNION ALL
SELECT 'Border Event', COUNT(*) FROM articles WHERE source IN ('foxnews.com', 'cnn.com', 'bbc.com', 'apnews.com', 'politico.com');

-- Check that events would appear in conflicts
SELECT COUNT(*) as total_conflict_events
FROM events
WHERE unique_sources >= 2
AND (category IN ('politics', 'international') OR category IS NULL);
