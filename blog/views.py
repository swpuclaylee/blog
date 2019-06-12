# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
import logging
from django.conf import settings
from models import *
from django.db.models import Count
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from forms import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login, logout, authenticate

logger = logging.getLogger('blog.views')

# Create your views here


def global_setting(request):
    # 站点基本信息
    SITE_URL = settings.SITE_URL
    SITE_NAME = settings.SITE_NAME
    SITE_DESC= settings.SITE_DESC
    WEIBO_SINA = settings.WEIBO_SINA
    WEIBO_TENCENT = settings.WEIBO_TENCENT
    PRO_RSS = settings.PRO_RSS
    PRO_EMAIL = settings.PRO_EMAIL


    # 分类信息获取（导航数据）
    category_list = Category.objects.all()

    # 归档信息
    archive_list = Article.objects.distinct_date()

    # 广告数据
    # 标签云
    tag_list = Tag.objects.all().reverse()

    # 友情链接
    link_list = Links.objects.all()

    # 评论排行
    comment_count_list = Comment.objects.values('article').annotate(comment_count=Count('article')).order_by('-comment_count')
    article_comment_list = [Article.objects.get(pk=comment['article']) for comment in comment_count_list]

    # 浏览排行
    browse_article_list = Article.objects.all().order_by('-click_count')

    # 站长推荐
    recommend_article_list = Article.objects.all().filter(is_recommend=True)

    return locals()


def index(request):
    try:
        # 最新文章获取
        article_list = getPage(request, Article.objects.all())
    except Exception as e:
        print e
        logger.error(e)
    return render(request, 'index.html', locals())


def archive(request):
    try:
        '''
        先获取客户端提交的信息
        '''
        year = request.GET.get('year', None)
        month = request.GET.get('month', None)
        article_list = getPage(request, Article.objects.filter(date_publish__icontains=year+'-'+month))
    except Exception as e:
        logger.error(e)
    return render(request, 'archive.html', locals())


def getPage(request, article_list):
    paginator = Paginator(article_list, 2)
    try:
        page = int(request.GET.get('page', 1))
        article_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        article_list = paginator.page(1)
    return article_list


def article(request):
    try:
        # 获取文章id
        id = request.GET.get('id', None)
        try:
            # 获取文章信息
            article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
            return render(request, 'failure.html', {'reason': '没有找到对应的文章'})

        # 评论表单
        comment_form = CommentForm({
            'author': request.user.username,
            'email': request.user.email,
            'url': request.user.url,
            'article': id
            } if request.user.is_authenticated() else {'article': id})
        comment_count = Comment.objects.filter(article=article).count()
        # 获取评论信息
        comments = Comment.objects.filter(article=article).order_by('id')
        comment_list = []
        for comment in comments:
            for item in comment_list:
                if not hasattr(item, 'children_comment'):
                    setattr(item, 'children_comment', [])
                if comment.pid == item:
                    item.children_comment.append(comment)
                    break
            if comment.pid is None:
                comment_list.append(comment)
    except Exception as e:
        logger.error(e)
    return render(request, 'article.html', locals())


# 提交评论
def comment_post(request):
    try:
        # 获取表单内填入的内容
        comment_form = CommentForm(request.POST)
        # 进行验证的第一个表单验证
        if comment_form.is_valid():
            # 获取表单信息
            # cleaned_data()用来把接收到的文字清洗为符合django的字符
            # create是一个在一步操作中同时创建对象并且保存的便捷方法。
            comment = Comment.objects.create(
                username=comment_form.cleaned_data["author"],
                email=comment_form.cleaned_data["email"],
                url=comment_form.cleaned_data["url"],
                content=comment_form.cleaned_data["comment"],
                article_id=comment_form.cleaned_data["article"],
                user=request.user if request.user.is_authenticated() else None
            )
            comment.save()
        else:
            return render(request, 'failure.html', {'reason': comment_form.errors})
    except Exception as e:
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])


def do_reg(request):
    try:
        if request.method == 'POST':
            reg_form = RegForm(request.POST)
            if reg_form.is_valid():
                # 注册
                user = User.objects.create(
                    username=reg_form.cleaned_data['username'],
                    email=reg_form.cleaned_data['email'],
                    url=reg_form.cleaned_data['url'],
                    password=make_password(reg_form.cleaned_data['password'])
                )
                user.save()
                # 登录
                user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                login(request, user)
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': reg_form.errors})
        else:
            reg_form = RegForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'reg.html', locals())


def do_login(request):
    try:
        if request.method == 'POST':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data['username']
                password = login_form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    user.backend = 'django.contrib.auth.backends.ModelBackend'  # 指定默认的登录验证方式
                    login(request, user)
                else:
                    return render(request, 'failure.html', {'reason': login_form.errors})
                return redirect(request.POST.get('source_url'))
        else:
            login_form = LoginForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'login.html', locals())


# 注销
def do_logout(request):
    try:
        logout(request)
    except Exception as e:
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])

