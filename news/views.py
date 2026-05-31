from django.shortcuts import render

# Create your views here.
import requests
from django.conf import settings
from newsapi import NewsApiClient

def news_view(request):
    newsapi = NewsApiClient(api_key=settings.NEWS_API_KEY)

    top_headlines = newsapi.get_top_headlines(
        country='us',
        language='en',
        category='business',
    )
    articles = top_headlines.get('articles', [])
    return render(request, 'new_home.html', {'articles': articles})