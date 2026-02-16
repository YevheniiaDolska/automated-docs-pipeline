#!/usr/bin/env python3
"""
Configurable Community Posts Fetcher
Легко адаптируется под любую платформу Community.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict
import requests

class CommunityFetcher:
    """Универсальный fetcher для разных Community платформ."""

    def __init__(self, platform_type: str = 'discourse', base_url: str = None):
        """
        Args:
            platform_type: Тип платформы (discourse, github-discussions, stackoverflow)
            base_url: Базовый URL Community
        """
        self.platform_type = platform_type
        self.base_url = base_url or os.environ.get('COMMUNITY_URL', 'https://community.n8n.io')
        self.api_key = os.environ.get('COMMUNITY_API_KEY', '')

    def fetch_discourse_posts(self, days: int = 7, min_views: int = 100) -> List[Dict]:
        """Получить посты из Discourse (n8n community и многие другие)."""
        posts = []

        # Discourse API endpoints
        endpoints = [
            f"/latest.json",  # Последние посты
            f"/top/weekly.json",  # Топ за неделю
            f"/categories.json"  # Категории для анализа
        ]

        headers = {
            'Api-Key': self.api_key,
            'Api-Username': 'system'
        } if self.api_key else {}

        for endpoint in endpoints[:2]:  # latest и top
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    params={'per_page': 100}
                )

                if response.status_code == 200:
                    data = response.json()

                    for topic in data.get('topic_list', {}).get('topics', []):
                        # Фильтруем по дате
                        created_at = datetime.fromisoformat(topic['created_at'].replace('Z', '+00:00'))
                        age_days = (datetime.now(created_at.tzinfo) - created_at).days

                        if age_days <= days and topic.get('views', 0) >= min_views:
                            posts.append({
                                'id': topic['id'],
                                'title': topic['title'],
                                'content': topic.get('excerpt', ''),
                                'views': topic.get('views', 0),
                                'replies': topic.get('posts_count', 1) - 1,
                                'likes': topic.get('like_count', 0),
                                'resolved': topic.get('solved', False),
                                'accepted_answer': topic.get('has_accepted_answer', False),
                                'created_date': created_at.isoformat(),
                                'category': topic.get('category_id'),
                                'tags': topic.get('tags', []),
                                'url': f"{self.base_url}/t/{topic['slug']}/{topic['id']}",
                                'platform': 'discourse'
                            })
            except Exception as e:
                print(f"Error fetching from {endpoint}: {e}")

        return posts

    def fetch_github_discussions(self, owner: str, repo: str, days: int = 7) -> List[Dict]:
        """Получить discussions из GitHub."""
        posts = []

        # GitHub GraphQL API
        query = """
        query($owner: String!, $repo: String!, $after: String) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
              nodes {
                id
                title
                body
                createdAt
                updatedAt
                answerChosenAt
                category { name }
                labels(first: 10) {
                  nodes { name }
                }
                comments { totalCount }
                upvoteCount
                url
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                'https://api.github.com/graphql',
                json={'query': query, 'variables': {'owner': owner, 'repo': repo}},
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()

                for discussion in data['data']['repository']['discussions']['nodes']:
                    created_at = datetime.fromisoformat(discussion['createdAt'].replace('Z', '+00:00'))
                    age_days = (datetime.now(created_at.tzinfo) - created_at).days

                    if age_days <= days:
                        posts.append({
                            'id': discussion['id'],
                            'title': discussion['title'],
                            'content': discussion['body'][:500],  # First 500 chars
                            'views': 0,  # GitHub doesn't provide view count
                            'replies': discussion['comments']['totalCount'],
                            'likes': discussion['upvoteCount'],
                            'resolved': bool(discussion['answerChosenAt']),
                            'accepted_answer': bool(discussion['answerChosenAt']),
                            'created_date': created_at.isoformat(),
                            'category': discussion['category']['name'],
                            'tags': [label['name'] for label in discussion['labels']['nodes']],
                            'url': discussion['url'],
                            'platform': 'github'
                        })
        except Exception as e:
            print(f"Error fetching GitHub discussions: {e}")

        return posts

    def fetch_stackoverflow(self, tag: str, days: int = 7) -> List[Dict]:
        """Получить вопросы из StackOverflow."""
        posts = []

        # StackOverflow API
        from_date = int((datetime.now() - timedelta(days=days)).timestamp())

        try:
            response = requests.get(
                'https://api.stackexchange.com/2.3/questions',
                params={
                    'fromdate': from_date,
                    'order': 'desc',
                    'sort': 'creation',
                    'tagged': tag,
                    'site': 'stackoverflow',
                    'filter': '!9_bDE(fI5'  # Include body
                }
            )

            if response.status_code == 200:
                data = response.json()

                for question in data.get('items', []):
                    created_at = datetime.fromtimestamp(question['creation_date'])

                    posts.append({
                        'id': question['question_id'],
                        'title': question['title'],
                        'content': question.get('body', '')[:500],
                        'views': question.get('view_count', 0),
                        'replies': question.get('answer_count', 0),
                        'likes': question.get('score', 0),
                        'resolved': question.get('is_answered', False),
                        'accepted_answer': bool(question.get('accepted_answer_id')),
                        'created_date': created_at.isoformat(),
                        'tags': question.get('tags', []),
                        'url': question['link'],
                        'platform': 'stackoverflow'
                    })
        except Exception as e:
            print(f"Error fetching StackOverflow questions: {e}")

        return posts

    def fetch_posts(self, days: int = 7, min_views: int = 100) -> List[Dict]:
        """Универсальный метод для получения постов."""

        if self.platform_type == 'discourse':
            return self.fetch_discourse_posts(days, min_views)

        elif self.platform_type == 'github':
            # Извлекаем owner/repo из URL
            parts = self.base_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                return self.fetch_github_discussions(parts[0], parts[1], days)

        elif self.platform_type == 'stackoverflow':
            # Тег передается через base_url для простоты
            tag = self.base_url or 'n8n'
            return self.fetch_stackoverflow(tag, days)

        else:
            print(f"Unknown platform type: {self.platform_type}")
            return []

def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Fetch community posts')
    parser.add_argument('--platform', default='discourse',
                        choices=['discourse', 'github', 'stackoverflow'],
                        help='Community platform type')
    parser.add_argument('--url', default=None,
                        help='Community base URL')
    parser.add_argument('--days', type=int, default=7,
                        help='Fetch posts from last N days')
    parser.add_argument('--min-views', type=int, default=100,
                        help='Minimum views threshold')
    parser.add_argument('--output', default='community-posts.json',
                        help='Output file')

    args = parser.parse_args()

    # Создаем fetcher
    fetcher = CommunityFetcher(
        platform_type=args.platform,
        base_url=args.url
    )

    # Получаем посты
    print(f"Fetching posts from {args.platform} for last {args.days} days...")
    posts = fetcher.fetch_posts(days=args.days, min_views=args.min_views)

    # Сохраняем результат
    with open(args.output, 'w') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'platform': args.platform,
            'days': args.days,
            'min_views': args.min_views,
            'total_posts': len(posts),
            'posts': posts
        }, f, indent=2)

    print(f"Saved {len(posts)} posts to {args.output}")

    # Выводим сводку
    if posts:
        total_views = sum(p.get('views', 0) for p in posts)
        unresolved = sum(1 for p in posts if not p.get('resolved', True))

        print(f"\nSummary:")
        print(f"- Total views: {total_views:,}")
        print(f"- Unresolved: {unresolved}")
        print(f"- Average replies: {sum(p.get('replies', 0) for p in posts) / len(posts):.1f}")

if __name__ == '__main__':
    main()
