"""Audit downloaded alternatives; produce research statistics, never train a model."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
OUTPUT = ROOT / 'findings'
OUTPUT.mkdir(exist_ok=True)


def counts(series):
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).items()}


def at_minute(path, column, minute, usecols=None):
    kept = []
    total = 0
    minute_counts = {}
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=100_000):
        total += len(chunk)
        for k, v in chunk[column].value_counts().items():
            minute_counts[str(k)] = minute_counts.get(str(k), 0) + int(v)
        kept.append(chunk.loc[chunk[column].eq(minute)].copy())
    return pd.concat(kept, ignore_index=True), total, minute_counts


folder = DATA / 'intervals-2026'
matches = pd.read_csv(folder / 'matches.csv')
players = pd.read_csv(folder / 'processed_summoner_data.csv')
columns = ['match_id', 'player_id', 'minute', 'total_gold', 'xp', 'level',
           'cs', 'jungle_cs', 'kills', 'deaths', 'assists', 'team_kills',
           'team_towers', 'team_inhibitors', 'team_dragons', 'team_barons',
           'team_void_grubs', 'team_heralds', 'team_gold_diff']
snapshots, total, minute_counts = at_minute(folder / 'intervals.csv', 'minute', 10, columns)
assert not players['id'].duplicated().any(), 'Duplicate player lookup keys'
assert not matches['match_id'].duplicated().any(), 'Duplicate match lookup keys'
joined = snapshots.merge(players[['id', 'match_id', 'team_id', 'participant_id']],
                         left_on=['player_id', 'match_id'], right_on=['id', 'match_id'],
                         how='left', validate='many_to_one')
team_sizes = joined.groupby(['match_id', 'team_id']).size().unstack(fill_value=0)
complete_ids = team_sizes.index[(team_sizes.get(100, 0) == 5) & (team_sizes.get(200, 0) == 5)]
data = joined[joined['match_id'].isin(complete_ids)].copy()
sum_fields = ['total_gold', 'xp', 'cs', 'jungle_cs', 'kills', 'deaths', 'assists']
team_agg = data.groupby(['match_id', 'team_id'])[sum_fields].sum()
team_agg['avg_level'] = data.groupby(['match_id', 'team_id'])['level'].mean()
objectives = ['team_dragons', 'team_barons', 'team_void_grubs', 'team_heralds']
objective_inconsistency = {}
for field in objectives:
    objective_inconsistency[field] = int((data.groupby(['match_id', 'team_id'])[field].nunique() > 1).sum())
    team_agg[field] = data.groupby(['match_id', 'team_id'])[field].first()
blue = team_agg.xs(100, level='team_id')
red = team_agg.xs(200, level='team_id')
features = pd.DataFrame(index=blue.index)
for field in team_agg.columns:
    features['blue_' + field] = blue[field]
    features['red_' + field] = red[field]
    features[field + '_diff'] = blue[field] - red[field]
features = features.reset_index().merge(matches, on='match_id', validate='one_to_one')
features['blueWins'] = features['winning_team'].eq(100).astype(int)
eligible = features['queue_id'].eq(420) & features['game_duration'].gt(600) & features['winning_team'].isin([100, 200])
eligible &= features['match_id'].str.startswith('EUW1_')
clean = features[eligible].copy()
clean_path = DATA / 'intervals-2026' / 'euw_10min_core.csv'
feature_names = [c for c in features if c.startswith(('blue_', 'red_')) or c.endswith('_diff')]
feature_names = [c for c in feature_names if c not in ['blue_bans', 'red_bans']]
clean = clean[['match_id', 'game_date', 'game_version'] + feature_names + ['blueWins']]
clean.to_csv(clean_path, index=False)
examples = pd.concat([clean[clean['blueWins'].eq(1)].head(1),
                      clean[clean['blueWins'].eq(0) & clean['total_gold_diff'].gt(0)].head(1),
                      clean[clean['blueWins'].eq(0) & clean['total_gold_diff'].le(0)].head(1)])
example_cols = ['match_id', 'total_gold_diff', 'xp_diff', 'kills_diff', 'team_dragons_diff', 'blueWins']
examples[example_cols].to_csv(OUTPUT / 'three_real_10min_examples.csv', index=False)
focused = clean[clean['game_version'].str.startswith(('16.1.', '16.2.'))].copy()
constant_features = [name for name in feature_names if focused[name].nunique() <= 1]
focused = focused.drop(columns=constant_features)
focused.to_csv(folder / 'euw_10min_patches_16_1_16_2.csv', index=False)
focused_examples = pd.concat([
    focused[focused['blueWins'].eq(1) & focused['total_gold_diff'].gt(0)].head(1),
    focused[focused['blueWins'].eq(0) & focused['total_gold_diff'].gt(0)].head(1),
    focused[focused['blueWins'].eq(1) & focused['total_gold_diff'].lt(0)].head(1),
])
focused_examples[example_cols].to_csv(OUTPUT / 'three_recent_10min_examples.csv', index=False)
reported_diff = data.groupby(['match_id', 'team_id'])['team_gold_diff'].first().unstack()
computed_diff = blue['total_gold'] - red['total_gold']
result = {'intervals_2026': {
    'matches_rows': len(matches), 'unique_matches': matches['match_id'].nunique(),
    'player_rows': len(players), 'interval_rows': total, 'interval_column_count': 36,
    'minute_counts': minute_counts, '10min_player_rows': len(snapshots),
    '10min_unique_matches': snapshots['match_id'].nunique(),
    '10min_duplicate_match_player_rows': int(snapshots.duplicated(['match_id', 'player_id']).sum()),
    'unmatched_player_rows': int(joined['team_id'].isna().sum()),
    'complete_10min_matches': len(complete_ids),
    'winning_team_counts_all_matches': counts(matches['winning_team']),
    'actual_platform_prefix_counts': counts(matches['match_id'].str.split('_').str[0]),
    'reported_region_counts': counts(matches['region']),
    'queue_counts': counts(matches['queue_id']), 'rank_counts_as_reported': counts(matches['average_rank']),
    'patch_counts': counts(matches['game_version'].str.split('.').str[:2].str.join('.')),
    'date_min': str(matches['game_date'].min()), 'date_max': str(matches['game_date'].max()),
    'derived_euw_10min_rows': len(clean), 'derived_feature_count': len(feature_names),
    'derived_blueWins_counts': counts(clean['blueWins']),
    'derived_missing_cells': int(clean.isna().sum().sum()),
    'team_objective_inconsistent_groups': objective_inconsistency,
    'stored_team_gold_diff_mismatches': int((reported_diff[100].reindex(computed_diff.index) != computed_diff).sum()),
    'derived_csv': str(clean_path), 'example_rows': examples[example_cols].to_dict(orient='records'),
    'focused_16_1_16_2_rows': len(focused),
    'focused_blueWins_counts': counts(focused['blueWins']),
    'focused_predictor_columns': len(focused.columns) - 4,
    'focused_constant_features_dropped': constant_features,
    'focused_date_min': focused['game_date'].min(), 'focused_date_max': focused['game_date'].max(),
    'focused_example_rows': focused_examples[example_cols].to_dict(orient='records'),
}}

folder = DATA / 'postmatch-timeline-2026'
match_table = pd.read_csv(folder / 'MatchTbl.csv')
player_matches = pd.read_csv(folder / 'SummonerMatchTbl.csv')
teams = pd.read_csv(folder / 'TeamMatchTbl.csv')
timeline10, total, minute_counts = at_minute(folder / 'MatchTimelineTbl.csv', 'Minute', 10,
                                           ['SummonerMatchFk', 'Minute', 'Win', 'TeamGoldDiff'])
mapped = timeline10.merge(player_matches[['SummonerMatchId', 'MatchFk']],
                          left_on='SummonerMatchFk', right_on='SummonerMatchId',
                          how='left', validate='many_to_one')
result['postmatch_timeline_2026'] = {
    'match_rows': len(match_table), 'player_match_rows': len(player_matches),
    'timeline_rows': total, 'minute_counts': minute_counts,
    '10min_player_rows': len(timeline10), '10min_unique_matches': mapped['MatchFk'].nunique(),
    'players_at_10min_per_match_counts': counts(mapped.groupby('MatchFk').size()),
    'blue_win_counts_from_team_table': counts(teams['BlueWin']),
    'platform_prefix_counts': counts(match_table['MatchId'].str.split('_').str[0]),
    'patch_counts': counts(match_table['Patch'].str.split('.').str[:2].str.join('.')),
    'missing_player_team_mapping': 'SummonerMatchTbl has no team_id; all-ten-player aggregation is not directly supported.',
}
apex = pd.read_csv(DATA / '14-minute-apex' / '14_data_EUW_Apex.csv')
result['apex_14min'] = {'rows': len(apex), 'unique_matches': apex['match_id'].nunique(),
                       'columns': list(apex), 'eventual_win_label_present': False}
original = pd.read_csv(DATA / 'original-10min' / 'high_diamond_ranked_10min.csv')
result['original_10min'] = {'rows': len(original), 'columns': len(original.columns),
                          'blueWins_counts': counts(original['blueWins']),
                          'missing_cells': int(original.isna().sum().sum())}
(OUTPUT / 'dataset-audit.json').write_text(json.dumps(result, indent=2, default=int), encoding='utf-8')
print(json.dumps(result, indent=2, default=int))
