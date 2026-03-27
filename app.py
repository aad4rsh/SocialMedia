import os
import json
import io
import base64
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# ─── Column category mappings ───
ENGAGEMENT_COLS = ['LikesCount', 'SharesCount', 'CommentsCount', 'ViewsCount']

TAG_CATEGORIES = {
    'Misinformation & Disinformation': {
        'parent': '21189:1:Misinformation & Disinformation',
        'children': {
            '21190:1a:false_claim': 'False Claim',
            '21191:1b:altered_content': 'Altered Content',
            '21192:1c:coordinated_content': 'Coordinated Content',
        }
    },
    'Hate Speech & Polarization': {
        'parent': '21193:2:Hate Speech & Polarization',
        'children': {
            '21194:2a:targeted_attack': 'Targeted Attack',
            '21195:2b:hate_incitement': 'Hate Incitement',
        }
    },
    'Electoral Integrity': {
        'parent': '21272:3:Electoral Integrity Narratives',
        'children': {
            '21273:3a:fraud': 'Fraud',
            '21274:3b:early_results': 'Early Results',
            '21275:3c:attack_election_commission': 'Attack Election Commission',
            '21276:3d:discredit_process': 'Discredit Process',
        }
    },
    'Gender & Inclusion': {
        'parent': '21202:4:Gender and Inclusion Dynamics',
        'children': {
            '21203:4a:attacks_on_women': 'Attacks on Women',
            '21204:4b:representation': 'Representation',
            '21205:4c:digital_barriers': 'Digital Barriers',
            '21261:4d:inclusion_policy_discussion': 'Inclusion Policy Discussion',
        }
    },
    'Target Group': {
        'parent': '21206:5:Target Group',
        'children': {
            '21207:5a:Women': 'Women',
            '21208:5b:Dalits': 'Dalits',
            '21209:5c:Janajati groups': 'Janajati Groups',
            '21210:5d:Madheshi communities': 'Madheshi Communities',
            '21211:5e:Religious minorities': 'Religious Minorities',
            '21212:5f:Journalists': 'Journalists',
            '21213:5g:Election officials': 'Election Officials',
            '21220:5h:Media': 'Media',
            '21221:5i:General Public': 'General Public',
        }
    },
    'Content Type': {
        'parent': '21214:6:Content Type',
        'children': {
            '21215:6a:Text post': 'Text Post',
            '21216:6b:Image': 'Image',
            '21217:6c:Video': 'Video',
            '21218:6d:AI-generated/deepfake content': 'AI/Deepfake',
            '21219:6e:Edited/repurposed content': 'Edited/Repurposed',
        }
    },
    'Tone': {
        'parent': '21222:7:Tone',
        'children': {
            '21223:7a:Positive': 'Positive',
            '21224:7b:Neutral': 'Neutral',
            '21225:7c:Negative': 'Negative',
            '21226:7d:Aggressive': 'Aggressive',
            '21227:7e:Fear-based': 'Fear-based',
            '21228:7f:Emotional': 'Emotional',
            '21229:7g:Informational': 'Informational',
        }
    },
    'Campaign Narrative': {
        'parent': '21230:8:Campaign Narrative',
        'children': {
            '21231:8a:Policy-based Message': 'Policy-based',
            '21232:8b:Issue-based Campaign': 'Issue-based',
            '21233:8c:Criticism/Attack on Opponent': 'Attack on Opponent',
            '21234:8d:Nationalism Sentiment': 'Nationalism',
            '21235:8e:Religious Appeal/Sentiment': 'Religious Appeal',
            '21236:8f:Trustbuilding': 'Trust Building',
            '21237:8g:Identity based Appeal': 'Identity Appeal',
            '21238:8h:Infrastructure Development Claim': 'Infrastructure Claim',
            '21239:8i:Neutral Information': 'Neutral Info',
            '21240:8j:Self-promotion': 'Self-promotion',
            '21243:8k:Political-party Promotion': 'Party Promotion',
            '21278:8l:Call to Vote': 'Call to Vote',
        }
    },
    'Political Party': {
        'parent': None,
        'children': {
            '21244:i:RSP': 'RSP',
            '21245:ii:UML': 'UML',
            '21246:iii:Congress': 'Congress',
            '21247:iv:NCP (Communist Party)': 'NCP',
            '21248:v:Others': 'Others',
        }
    },
    'Issue Area': {
        'parent': None,
        'children': {
            '21249:i:women': 'Women Issues',
            '21250:ii:marginalized_group': 'Marginalized Groups',
            '21251:iii:journalists': 'Journalists Issues',
            '21252:iv :public institutions': 'Public Institutions',
            '21253:v:religion': 'Religion',
            '21254:i:health': 'Health',
            '21255:ii:education': 'Education',
            '21256:vi:caste_based_attack': 'Caste-based Attack',
            '21257:vii:ethnic_or_regional_identity_attack': 'Ethnic/Regional Attack',
            '21258:viii:inclusion_policy_discussion': 'Inclusion Policy',
            '21259:ix:intersectional_attack': 'Intersectional Attack',
            '21260:x:political party': 'Political Party Issues',
            '21262:iii:basic needs': 'Basic Needs',
            '21263:iv:transportation': 'Transportation',
            '21264:v:security': 'Security',
            '21265:vi:employment': 'Employment',
            '21266:vii:foreign policy': 'Foreign Policy',
            '21267:viii:tech sector': 'Tech Sector',
            '21268:ix:environment': 'Environment',
            '21269:x:social media': 'Social Media Issues',
            '21270:xi:inclusion and representation': 'Inclusion & Representation',
            '21271:xii:others': 'Others',
        }
    },
}


def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def parse_csv(file_content):
    """Parse the uploaded CSV and clean it."""
    df = pd.read_csv(io.BytesIO(file_content), sep='\t', encoding='utf-8', on_bad_lines='warn')

    # If tab-separated fails, try comma
    if len(df.columns) < 5:
        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8', on_bad_lines='warn')

    # Convert engagement columns to numeric
    for col in ENGAGEMENT_COLS:
        if col in df.columns:
            df[col] = df[col].apply(safe_int)

    # Parse dates
    if 'PublishedAt' in df.columns:
        df['PublishedAt'] = pd.to_datetime(df['PublishedAt'], errors='coerce', utc=True)

    # Convert binary tag columns to numeric
    for cat_name, cat_info in TAG_CATEGORIES.items():
        if cat_info['parent'] and cat_info['parent'] in df.columns:
            df[cat_info['parent']] = pd.to_numeric(df[cat_info['parent']], errors='coerce').fillna(0).astype(int)
        for col_name in cat_info['children'].keys():
            if col_name in df.columns:
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0).astype(int)

    return df


def compute_overview(df):
    """Basic dataset overview stats."""
    total_posts = len(df)

    # Engagement
    eng = {}
    for col in ENGAGEMENT_COLS:
        if col in df.columns:
            eng[col] = {
                'total': int(df[col].sum()),
                'mean': round(float(df[col].mean()), 2),
                'median': round(float(df[col].median()), 2),
                'max': int(df[col].max()),
                'std': round(float(df[col].std()), 2),
            }

    # Platform distribution
    platform_dist = {}
    if 'Platform' in df.columns:
        platform_dist = df['Platform'].value_counts().to_dict()

    # Channel / politician distribution
    channel_dist = {}
    if 'ChannelName' in df.columns:
        channel_dist = df['ChannelName'].value_counts().head(20).to_dict()

    # Date range
    date_range = {}
    if 'PublishedAt' in df.columns:
        valid_dates = df['PublishedAt'].dropna()
        if len(valid_dates) > 0:
            date_range = {
                'earliest': str(valid_dates.min()),
                'latest': str(valid_dates.max()),
                'span_days': (valid_dates.max() - valid_dates.min()).days
            }

    # Post types
    post_type_dist = {}
    if 'PostType' in df.columns:
        post_type_dist = df['PostType'].value_counts().to_dict()

    return {
        'total_posts': total_posts,
        'columns_count': len(df.columns),
        'engagement': eng,
        'platform_distribution': platform_dist,
        'channel_distribution': channel_dist,
        'date_range': date_range,
        'post_type_distribution': post_type_dist,
    }


def compute_tag_analysis(df):
    """Analyze tag distributions across all categories."""
    results = {}
    for cat_name, cat_info in TAG_CATEGORIES.items():
        cat_data = {}
        for col_name, label in cat_info['children'].items():
            if col_name in df.columns:
                count = int(df[col_name].sum())
                cat_data[label] = count
        if cat_data:
            results[cat_name] = cat_data
    return results


def compute_engagement_by_tag(df):
    """Average engagement metrics per tag."""
    results = {}
    for cat_name, cat_info in TAG_CATEGORIES.items():
        cat_data = {}
        for col_name, label in cat_info['children'].items():
            if col_name in df.columns:
                tagged_posts = df[df[col_name] == 1]
                if len(tagged_posts) > 0:
                    cat_data[label] = {
                        'count': len(tagged_posts),
                        'avg_likes': round(float(tagged_posts['LikesCount'].mean()), 2) if 'LikesCount' in df.columns else 0,
                        'avg_shares': round(float(tagged_posts['SharesCount'].mean()), 2) if 'SharesCount' in df.columns else 0,
                        'avg_comments': round(float(tagged_posts['CommentsCount'].mean()), 2) if 'CommentsCount' in df.columns else 0,
                        'total_engagement': int(tagged_posts[ENGAGEMENT_COLS].sum().sum()) if all(c in df.columns for c in ENGAGEMENT_COLS) else 0,
                    }
        if cat_data:
            results[cat_name] = cat_data
    return results


def compute_insights(df, tag_analysis, engagement_by_tag):
    """Generate text-based insights from the data."""
    insights = []

    total = len(df)

    # 1. Misinformation insight
    misinfo_tags = tag_analysis.get('Misinformation & Disinformation', {})
    misinfo_total = sum(misinfo_tags.values())
    if misinfo_total > 0:
        pct = round(misinfo_total / total * 100, 1)
        top_type = max(misinfo_tags, key=misinfo_tags.get) if misinfo_tags else 'N/A'
        insights.append({
            'category': 'Misinformation',
            'icon': '⚠️',
            'title': f'{pct}% of posts flagged for Misinformation/Disinformation',
            'detail': f'{misinfo_total} posts out of {total} contain misinformation indicators. The most common type is "{top_type}" ({misinfo_tags.get(top_type, 0)} posts).',
            'severity': 'high' if pct > 10 else 'medium'
        })

    # 2. Hate speech insight
    hate_tags = tag_analysis.get('Hate Speech & Polarization', {})
    hate_total = sum(hate_tags.values())
    if hate_total > 0:
        pct = round(hate_total / total * 100, 1)
        insights.append({
            'category': 'Hate Speech',
            'icon': '🔴',
            'title': f'{pct}% of posts contain Hate Speech/Polarization',
            'detail': f'{hate_total} posts flagged for hate speech or polarization content.',
            'severity': 'high' if pct > 5 else 'medium'
        })

    # 3. Tone analysis
    tone_tags = tag_analysis.get('Tone', {})
    if tone_tags:
        total_tone = sum(tone_tags.values())
        if total_tone > 0:
            negative_tones = sum(tone_tags.get(t, 0) for t in ['Negative', 'Aggressive', 'Fear-based'])
            positive_tones = tone_tags.get('Positive', 0)
            neg_pct = round(negative_tones / total_tone * 100, 1)
            pos_pct = round(positive_tones / total_tone * 100, 1)
            dominant = max(tone_tags, key=tone_tags.get)
            insights.append({
                'category': 'Tone',
                'icon': '🎭',
                'title': f'Dominant tone: {dominant}',
                'detail': f'{neg_pct}% negative/aggressive/fear-based vs {pos_pct}% positive. The overall discourse leans {"negative" if neg_pct > pos_pct else "positive"}.',
                'severity': 'high' if neg_pct > 40 else 'low'
            })

    # 4. Campaign narrative
    campaign_tags = tag_analysis.get('Campaign Narrative', {})
    if campaign_tags:
        dominant_narrative = max(campaign_tags, key=campaign_tags.get)
        attack_count = campaign_tags.get('Attack on Opponent', 0)
        policy_count = campaign_tags.get('Policy-based', 0)
        insights.append({
            'category': 'Campaign',
            'icon': '📢',
            'title': f'Dominant campaign narrative: {dominant_narrative}',
            'detail': f'Attack-on-opponent posts: {attack_count}, Policy-based posts: {policy_count}. {"Campaigns are more attack-oriented than policy-driven." if attack_count > policy_count else "Campaigns lean towards policy-based messaging."}',
            'severity': 'medium'
        })

    # 5. Target group analysis
    target_tags = tag_analysis.get('Target Group', {})
    if target_tags:
        most_targeted = max(target_tags, key=target_tags.get)
        insights.append({
            'category': 'Target Groups',
            'icon': '🎯',
            'title': f'Most targeted group: {most_targeted}',
            'detail': f'{most_targeted} is the most frequently targeted group with {target_tags[most_targeted]} posts.',
            'severity': 'medium'
        })

    # 6. Electoral integrity
    electoral_tags = tag_analysis.get('Electoral Integrity', {})
    electoral_total = sum(electoral_tags.values())
    if electoral_total > 0:
        insights.append({
            'category': 'Electoral Integrity',
            'icon': '🗳️',
            'title': f'{electoral_total} posts challenge electoral integrity',
            'detail': f'Posts questioning electoral processes, including fraud claims, attacks on election commission, and attempts to discredit the process.',
            'severity': 'high' if electoral_total > 20 else 'medium'
        })

    # 7. Gender dynamics
    gender_tags = tag_analysis.get('Gender & Inclusion', {})
    if gender_tags:
        attacks_women = gender_tags.get('Attacks on Women', 0)
        if attacks_women > 0:
            insights.append({
                'category': 'Gender',
                'icon': '♀️',
                'title': f'{attacks_women} posts contain attacks on women',
                'detail': f'Gender-based attacks detected. Representation posts: {gender_tags.get("Representation", 0)}, Digital barriers: {gender_tags.get("Digital Barriers", 0)}.',
                'severity': 'high'
            })

    # 8. Most engaging content
    if 'LikesCount' in df.columns:
        df['TotalEngagement'] = df[ENGAGEMENT_COLS].sum(axis=1)
        top_post = df.nlargest(1, 'TotalEngagement')
        if len(top_post) > 0:
            tp = top_post.iloc[0]
            channel = tp.get('ChannelName', 'Unknown')
            eng_val = int(tp['TotalEngagement'])
            insights.append({
                'category': 'Engagement',
                'icon': '🔥',
                'title': f'Most engaging post: {eng_val:,} total interactions',
                'detail': f'By {channel} on {tp.get("Platform", "Unknown")}. Likes: {safe_int(tp.get("LikesCount", 0)):,}, Shares: {safe_int(tp.get("SharesCount", 0)):,}, Comments: {safe_int(tp.get("CommentsCount", 0)):,}.',
                'severity': 'low'
            })

    # 9. Platform comparison
    if 'Platform' in df.columns and 'LikesCount' in df.columns:
        platform_eng = df.groupby('Platform')[ENGAGEMENT_COLS].mean().round(2)
        if len(platform_eng) > 1:
            best_platform = platform_eng.sum(axis=1).idxmax()
            insights.append({
                'category': 'Platform',
                'icon': '📊',
                'title': f'Highest average engagement platform: {best_platform}',
                'detail': f'{best_platform} generates the highest average engagement per post across all metrics.',
                'severity': 'low'
            })

    # 10. Content type insight
    content_tags = tag_analysis.get('Content Type', {})
    if content_tags:
        dominant_type = max(content_tags, key=content_tags.get)
        insights.append({
            'category': 'Content',
            'icon': '📝',
            'title': f'Most common content type: {dominant_type}',
            'detail': f'{dominant_type} posts dominate with {content_tags[dominant_type]} posts ({round(content_tags[dominant_type]/total*100, 1)}% of all content).',
            'severity': 'low'
        })

    return insights


def generate_charts(df, tag_analysis, engagement_by_tag):
    """Generate Plotly chart JSON for the frontend."""
    charts = []
    colors = px.colors.qualitative.Set3

    # ── 1. Platform Distribution Pie ──
    if 'Platform' in df.columns:
        platform_counts = df['Platform'].value_counts()
        fig = go.Figure(data=[go.Pie(
            labels=platform_counts.index.tolist(),
            values=platform_counts.values.tolist(),
            hole=0.45,
            marker=dict(colors=['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#818cf8']),
            textinfo='label+percent',
            textfont=dict(size=13),
        )])
        fig.update_layout(
            title=dict(text='Platform Distribution', font=dict(size=18, color='#e2e8f0')),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            legend=dict(font=dict(size=12)),
            margin=dict(t=50, b=30, l=30, r=30),
        )
        charts.append({'id': 'platform_dist', 'title': 'Platform Distribution', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 2. Engagement Over Time ──
    if 'PublishedAt' in df.columns:
        time_df = df.dropna(subset=['PublishedAt']).copy()
        if len(time_df) > 0:
            time_df['Date'] = time_df['PublishedAt'].dt.date
            daily = time_df.groupby('Date')[ENGAGEMENT_COLS].sum().reset_index()
            fig = go.Figure()
            colors_line = ['#6366f1', '#22d3ee', '#f472b6', '#facc15']
            for i, col in enumerate(ENGAGEMENT_COLS):
                if col in daily.columns:
                    fig.add_trace(go.Scatter(
                        x=daily['Date'], y=daily[col],
                        mode='lines+markers', name=col.replace('Count', ''),
                        line=dict(color=colors_line[i], width=2),
                        marker=dict(size=4),
                    ))
            fig.update_layout(
                title=dict(text='Engagement Over Time', font=dict(size=18, color='#e2e8f0')),
                xaxis=dict(title='Date', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
                yaxis=dict(title='Count', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                legend=dict(font=dict(size=12)),
                margin=dict(t=50, b=50, l=50, r=30),
                hovermode='x unified',
            )
            charts.append({'id': 'engagement_time', 'title': 'Engagement Timeline', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 3. Tag Category Bar Charts ──
    for cat_name, cat_data in tag_analysis.items():
        if cat_data and sum(cat_data.values()) > 0:
            sorted_data = dict(sorted(cat_data.items(), key=lambda x: x[1], reverse=True))
            labels = list(sorted_data.keys())
            values = list(sorted_data.values())

            fig = go.Figure(data=[go.Bar(
                x=values, y=labels,
                orientation='h',
                marker=dict(
                    color=values,
                    colorscale='Viridis',
                    line=dict(width=0),
                ),
                text=values,
                textposition='outside',
                textfont=dict(size=12, color='#cbd5e1'),
            )])
            fig.update_layout(
                title=dict(text=f'{cat_name} Distribution', font=dict(size=18, color='#e2e8f0')),
                xaxis=dict(title='Number of Posts', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
                yaxis=dict(color='#94a3b8', autorange='reversed'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                margin=dict(t=50, b=50, l=160, r=60),
                height=max(300, len(labels) * 35 + 100),
            )
            safe_id = cat_name.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
            charts.append({'id': f'tag_{safe_id}', 'title': f'{cat_name} Distribution', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 4. Top Channels by Total Engagement ──
    if 'ChannelName' in df.columns and 'LikesCount' in df.columns:
        df['TotalEngagement'] = df[ENGAGEMENT_COLS].sum(axis=1)
        channel_eng = df.groupby('ChannelName')['TotalEngagement'].sum().nlargest(15).reset_index()
        fig = go.Figure(data=[go.Bar(
            x=channel_eng['TotalEngagement'],
            y=channel_eng['ChannelName'],
            orientation='h',
            marker=dict(color=channel_eng['TotalEngagement'], colorscale='Magma'),
            text=channel_eng['TotalEngagement'].apply(lambda x: f'{x:,}'),
            textposition='outside',
            textfont=dict(size=11, color='#cbd5e1'),
        )])
        fig.update_layout(
            title=dict(text='Top 15 Channels by Total Engagement', font=dict(size=18, color='#e2e8f0')),
            xaxis=dict(title='Total Engagement', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
            yaxis=dict(color='#94a3b8', autorange='reversed'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            margin=dict(t=50, b=50, l=150, r=80),
            height=500,
        )
        charts.append({'id': 'top_channels', 'title': 'Top Channels by Engagement', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 5. Tone vs Campaign Narrative Heatmap ──
    tone_tags = tag_analysis.get('Tone', {})
    campaign_tags = tag_analysis.get('Campaign Narrative', {})
    if tone_tags and campaign_tags:
        tone_cols = {col: label for col, label in TAG_CATEGORIES['Tone']['children'].items() if col in df.columns}
        camp_cols = {col: label for col, label in TAG_CATEGORIES['Campaign Narrative']['children'].items() if col in df.columns}
        if tone_cols and camp_cols:
            matrix = []
            for tc, tl in tone_cols.items():
                row = []
                for cc, cl in camp_cols.items():
                    count = int(((df[tc] == 1) & (df[cc] == 1)).sum())
                    row.append(count)
                matrix.append(row)

            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=[cl for cl in camp_cols.values()],
                y=[tl for tl in tone_cols.values()],
                colorscale='Viridis',
                text=matrix,
                texttemplate='%{text}',
                textfont=dict(size=11),
            ))
            fig.update_layout(
                title=dict(text='Tone × Campaign Narrative Correlation', font=dict(size=18, color='#e2e8f0')),
                xaxis=dict(color='#94a3b8', tickangle=45),
                yaxis=dict(color='#94a3b8'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                margin=dict(t=50, b=120, l=120, r=30),
                height=450,
            )
            charts.append({'id': 'tone_campaign_heatmap', 'title': 'Tone × Campaign Narrative', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 6. Engagement Distribution Box Plot ──
    if all(c in df.columns for c in ENGAGEMENT_COLS):
        fig = go.Figure()
        box_colors = ['#6366f1', '#22d3ee', '#f472b6', '#facc15']
        for i, col in enumerate(ENGAGEMENT_COLS):
            fig.add_trace(go.Box(
                y=df[col], name=col.replace('Count', ''),
                marker_color=box_colors[i],
                boxmean=True,
            ))
        fig.update_layout(
            title=dict(text='Engagement Distribution', font=dict(size=18, color='#e2e8f0')),
            yaxis=dict(title='Count', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)', type='log'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            margin=dict(t=50, b=50, l=50, r=30),
            showlegend=False,
        )
        charts.append({'id': 'engagement_box', 'title': 'Engagement Distribution', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 7. Posts per Day Histogram ──
    if 'PublishedAt' in df.columns:
        time_df = df.dropna(subset=['PublishedAt']).copy()
        if len(time_df) > 0:
            time_df['Date'] = time_df['PublishedAt'].dt.date
            daily_counts = time_df.groupby('Date').size().reset_index(name='PostCount')
            fig = go.Figure(data=[go.Bar(
                x=daily_counts['Date'],
                y=daily_counts['PostCount'],
                marker=dict(color='#6366f1', opacity=0.8),
            )])
            fig.update_layout(
                title=dict(text='Posts Per Day', font=dict(size=18, color='#e2e8f0')),
                xaxis=dict(title='Date', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
                yaxis=dict(title='Number of Posts', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                margin=dict(t=50, b=50, l=50, r=30),
                bargap=0.1,
            )
            charts.append({'id': 'posts_per_day', 'title': 'Daily Post Volume', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 8. Engagement by Content Type ──
    content_engagement = engagement_by_tag.get('Content Type', {})
    if content_engagement:
        labels = list(content_engagement.keys())
        avg_likes = [content_engagement[l]['avg_likes'] for l in labels]
        avg_shares = [content_engagement[l]['avg_shares'] for l in labels]
        avg_comments = [content_engagement[l]['avg_comments'] for l in labels]

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Avg Likes', x=labels, y=avg_likes, marker_color='#6366f1'))
        fig.add_trace(go.Bar(name='Avg Shares', x=labels, y=avg_shares, marker_color='#22d3ee'))
        fig.add_trace(go.Bar(name='Avg Comments', x=labels, y=avg_comments, marker_color='#f472b6'))
        fig.update_layout(
            barmode='group',
            title=dict(text='Avg Engagement by Content Type', font=dict(size=18, color='#e2e8f0')),
            xaxis=dict(color='#94a3b8'),
            yaxis=dict(title='Average Count', color='#94a3b8', gridcolor='rgba(148,163,184,0.1)'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            legend=dict(font=dict(size=12)),
            margin=dict(t=50, b=50, l=50, r=30),
        )
        charts.append({'id': 'engagement_content_type', 'title': 'Engagement by Content Type', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 9. Engagement by Tone Radar ──
    tone_engagement = engagement_by_tag.get('Tone', {})
    if tone_engagement:
        labels = list(tone_engagement.keys())
        avg_eng = [tone_engagement[l]['avg_likes'] + tone_engagement[l]['avg_shares'] + tone_engagement[l]['avg_comments'] for l in labels]

        fig = go.Figure(data=go.Scatterpolar(
            r=avg_eng + [avg_eng[0]],
            theta=labels + [labels[0]],
            fill='toself',
            fillcolor='rgba(99,102,241,0.3)',
            line=dict(color='#6366f1', width=2),
            marker=dict(size=6),
        ))
        fig.update_layout(
            title=dict(text='Engagement by Tone (Radar)', font=dict(size=18, color='#e2e8f0')),
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(gridcolor='rgba(148,163,184,0.2)', color='#94a3b8'),
                angularaxis=dict(gridcolor='rgba(148,163,184,0.2)', color='#94a3b8'),
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            margin=dict(t=60, b=30, l=60, r=60),
        )
        charts.append({'id': 'tone_radar', 'title': 'Engagement by Tone', 'data': json.loads(plotly.io.to_json(fig))})

    # ── 10. Misinformation & Hate Speech Sunburst ──
    sun_labels = ['All Issues']
    sun_parents = ['']
    sun_values = [0]

    for cat_name in ['Misinformation & Disinformation', 'Hate Speech & Polarization', 'Electoral Integrity', 'Gender & Inclusion']:
        cat_data = tag_analysis.get(cat_name, {})
        if cat_data:
            total_cat = sum(cat_data.values())
            sun_labels.append(cat_name)
            sun_parents.append('All Issues')
            sun_values.append(total_cat)
            for label, count in cat_data.items():
                if count > 0:
                    sun_labels.append(label)
                    sun_parents.append(cat_name)
                    sun_values.append(count)

    if len(sun_labels) > 1:
        fig = go.Figure(go.Sunburst(
            labels=sun_labels,
            parents=sun_parents,
            values=sun_values,
            branchvalues='total',
            marker=dict(colorscale='RdYlGn_r'),
            textfont=dict(size=12),
        ))
        fig.update_layout(
            title=dict(text='Content Issues Breakdown', font=dict(size=18, color='#e2e8f0')),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            margin=dict(t=50, b=30, l=30, r=30),
            height=500,
        )
        charts.append({'id': 'issues_sunburst', 'title': 'Content Issues Breakdown', 'data': json.loads(plotly.io.to_json(fig))})

    return charts


# ─── Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400

    try:
        content = file.read()
        df = parse_csv(content)

        overview = compute_overview(df)
        tag_analysis = compute_tag_analysis(df)
        engagement_by_tag = compute_engagement_by_tag(df)
        insights = compute_insights(df, tag_analysis, engagement_by_tag)
        charts = generate_charts(df, tag_analysis, engagement_by_tag)

        # Compute a summary for the report header
        filename = file.filename
        channels = df['ChannelName'].nunique() if 'ChannelName' in df.columns else 0

        return jsonify({
            'success': True,
            'filename': filename,
            'overview': overview,
            'tag_analysis': tag_analysis,
            'engagement_by_tag': engagement_by_tag,
            'insights': insights,
            'charts': charts,
            'summary': {
                'filename': filename,
                'total_posts': overview['total_posts'],
                'unique_channels': channels,
                'platforms': list(overview['platform_distribution'].keys()),
                'date_range': overview['date_range'],
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
