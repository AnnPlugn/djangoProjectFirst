
import json
import logging
import os
from pathlib import Path
from typing import List
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from omegaconf import OmegaConf
from loguru import logger
from pymongo import MongoClient
from django.conf import settings
from .GXP_AI_agent.core.vectordb.vectore_store import VectorDB
from .GXP_AI_agent.core.vectordb.index import Index
from .GXP_AI_agent.core.llm.rag_pipeline import RAG
from .GXP_AI_agent.core.llm.model import OpenAILLM
from .GXP_AI_agent.core.embeddings.model import LocalEmbeddings
from .GXP_AI_agent.core.prompts.llm_prompt import rag_prompt
from .models import Compound
from .forms import RegistrationForm, LoginForm
from .scraper.utils import extract_property_data, is_valid_url

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Django logger for errors only
logger.remove()  # Remove default loguru handler
logger.add("document_load.log", rotation="10 MB", level="ERROR")  # Log errors to file

# Initialize MongoDB client
MONGO_CLIENT = MongoClient('mongodb://127.0.0.1:27017/')
MONGO_DB = MONGO_CLIENT['django_vector_db']
MONGO_COLLECTION_DOCS = MONGO_DB['documents']
MONGO_COLLECTION_INDEX = MONGO_DB['index_to_docstore_id']


# RAG Model Holder
class RAGModelHolder:
    _instance = None

    def __init__(self):
        if not hasattr(settings, 'CONFIGURED') or not settings.CONFIGURED:
            raise RuntimeError("Django settings not configured")

        try:
            # Формируем путь к config.yaml относительно корня проекта
            config_path = os.path.join(settings.BASE_DIR, 'firstblog', 'GXP_AI_agent', 'config', 'config.yaml')
            conf = OmegaConf.load(config_path)

            # Базовая директория для путей данных
            base_data_dir = os.path.join(settings.BASE_DIR, 'firstblog', 'GXP_AI_agent')

            # Преобразуем относительные пути из YAML в абсолютные
            conf.data_config.path = os.path.join(base_data_dir, conf.data_config.path)
            conf.data_config.save_path = os.path.join(base_data_dir, conf.data_config.save_path)
            conf.faiss_config.store.data_path = os.path.join(base_data_dir, conf.faiss_config.store.data_path)

            self.llm = OpenAILLM(conf.llm.chatgpt_config)
            self.embeddings = LocalEmbeddings(conf.embeddings.ollama_config)
            self.index = Index(self.embeddings.get_size_of_embeddings())
            self.store = VectorDB(
                conf.faiss_config.store.data_path,
                self.embeddings.model,
                self.index.index
            )
            self.model = RAG(
                self.store,
                self.llm,
                rag_prompt,
                conf.faiss_config.search_config.retriever
            )
            self.initialized = True
        except Exception as e:
            print(f"Error initializing RAG model: {str(e)}")
            self.initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


rag_holder = RAGModelHolder.get_instance()
def home(request):
    if request.method == 'POST':
        input_data = request.POST.get('input_data', '')
        model_output = f"Анализ данных: {input_data}"
        return render(request, 'blog/home.html', {'model_output': model_output})
    return render(request, 'blog/home.html')


def about(request):
    return render(request, 'blog/about.html')


@csrf_exempt
def invoke_model(request):
    if request.method == 'POST':
        input_data = request.POST.get('input_data', '')
        model_output = f"Результат модели для: {input_data}"
        Compound.objects.create(
            name=input_data[:50],
            formula='N/A',
            description=model_output
        )
        return JsonResponse({'message': model_output})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def result(request):
    try:
        if not rag_holder.initialized:
            logger.error("RAG model not initialized")
            return render(request, 'result.html', {'error': 'RAG model not initialized', 'status': 'error'})

        if request.method == 'POST':
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                      request.content_type == 'application/json'
            if is_ajax and request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON data")
                    return JsonResponse({'error': 'Invalid JSON data', 'status': 'error'}, status=400)
            else:
                data = request.POST

            query = data.get('query', '').strip()
            if not query:
                response = {'error': 'Query is required', 'status': 'error'}
                return JsonResponse(response, status=400) if is_ajax else \
                    render(request, 'result.html', response)

            try:
                logger.info(f"Processing query: {query}")
                result = rag_holder.model.invoke(query)
                if isinstance(result, dict) and 'context' in result and 'answer' in result:
                    answer_content = result['answer'].content if hasattr(result['answer'], 'content') else str(
                        result['answer'])
                    context_cleaned = [item.split('texts/')[-1] for item in result['context']]
                    response = {
                        'context': context_cleaned,
                        'answer': answer_content.split('\n'),
                        'status': 'success'
                    }
                else:
                    response = {
                        'answer': str(result).split('\n'),
                        'context': [],
                        'status': 'success'
                    }
                return JsonResponse(response) if is_ajax else render(request, 'result.html', response)
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                response = {'error': str(e), 'status': 'error'}
                return JsonResponse(response, status=500) if is_ajax else \
                    render(request, 'result.html', response)
        return render(request, 'result.html')
    except Exception as e:
        logger.error(f"Error in result view: {e}")
        return render(request, 'result.html', {'error': str(e), 'status': 'error'})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            status = form.cleaned_data['status']
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                if status == 'admin':
                    group, _ = Group.objects.get_or_create(name='Admins')
                    user.groups.add(group)
                user.save()
                auth_login(request, user)
                return redirect('firstblog:home')
            except Exception as e:
                logger.error(f"Error during registration: {e}")
                form.add_error(None, str(e))
        return render(request, 'register.html', {'form': form})
    return render(request, 'register.html', {'form': RegistrationForm()})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                request.session.set_expiry(1209600 if remember_me else 0)
                return redirect('firstblog:home')
            else:
                logger.error("Invalid login attempt")
                form.add_error(None, 'Неверный логин или пароль')
                return render(request, 'login.html', {'form': form, 'show_register': True})
        return render(request, 'login.html', {'form': form, 'show_register': True})
    return render(request, 'login.html', {'form': LoginForm()})


def logout(request):
    auth_logout(request)
    return redirect('firstblog:home')

