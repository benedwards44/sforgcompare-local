from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, Template, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from compareorgs.models import Job, Org, ComponentType, Component, ComponentListUnique, OfflineFileJob
from compareorgs.forms import JobForm
import json	
import requests
import datetime
import uuid
from time import sleep
from compareorgs.tasks import download_metadata_metadata, download_metadata_tooling
import sys
import sqlite3
import os
from zipfile import ZipFile
import StringIO
import traceback

from suds.client import Client

reload(sys)
sys.setdefaultencoding("utf-8")

def index(request):
	"""
	Home page for the application. Holds the methods to authenticate and begin the process

	"""

	if request.POST:

		job_form = JobForm(request.POST)

		if job_form.is_valid():

			job = Job()
			job.created_date = datetime.datetime.now()
			job.status = 'Not Started'
			job.contextual_diff = job_form.cleaned_data['contextual_diff']
			job.random_id = uuid.uuid4()
			job.save()

			org_one = Org()
			org_one.username = job_form.cleaned_data['org_one_username']
			org_one.access_token = job_form.cleaned_data['org_one_session_id']
			org_one.instance_url = job_form.cleaned_data['org_one_metadata_url']
			org_one.org_id = job_form.cleaned_data['org_one_org_id']
			org_one.org_name = job_form.cleaned_data['org_one_org_name']
			org_one.org_number = 1
			org_one.job = job
			org_one.save()

			org_two = Org()
			org_two.username = job_form.cleaned_data['org_two_username']
			org_two.access_token = job_form.cleaned_data['org_two_session_id']
			org_two.instance_url = job_form.cleaned_data['org_two_metadata_url']
			org_two.org_id = job_form.cleaned_data['org_two_org_id']
			org_two.org_name = job_form.cleaned_data['org_two_org_name']
			org_two.org_number = 1
			org_two.job = job
			org_two.save()

			return HttpResponseRedirect('/compare_orgs/' + str(job.random_id) + '/?api=' + job_form.cleaned_data['api_choice'])

	else:
		job_form = JobForm()

	return render_to_response(
		'index.html', 
		RequestContext(request,{'job_form': job_form}
	))

# AJAX endpoint for page to constantly check if job is finished
def job_status(request, job_id):

	job = get_object_or_404(Job, random_id = job_id)

	response_data = {
		'status': job.status,
		'error': job.error
	}

	return HttpResponse(json.dumps(response_data), content_type = 'application/json')

# Page for user to wait for job to run
def compare_orgs(request, job_id):

	job = get_object_or_404(Job, random_id = job_id)

	if job.status == 'Not Started':

		api_choice = request.GET.get('api')

		job.status = 'Downloading Metadata'
		job.api_choice = api_choice
		job.save()

		# Do logic for job
		for org in job.org_set.all():

			if api_choice == 'metadata':

				try:

					download_metadata_metadata(job, org)

				except Exception as error:

					org.status = 'Error'
					org.error = error
					org.save()

					job.status = 'Error'
					job.error = error
					job.error_stacktrace = traceback.format_exc()
					job.save()

			else:

				try:

					download_metadata_tooling(job, org)

				except Exception as error:

					org.status = 'Error'
					org.error = error
					org.save()

					job.status = 'Error'
					job.error = error
					job.error_stacktrace = traceback.format_exc()
					job.save()

	elif job.status == 'Finished':

		# Return URL when job is finished
		return_url = '/compare_result/' + str(job.random_id) + '/'
		return HttpResponseRedirect(return_url)

	return render_to_response('loading.html', RequestContext(request, {'job': job}))	

# Page to display compare results
def compare_results(request, job_id):

	job = get_object_or_404(Job, random_id = job_id)

	if job.status != 'Finished':
		return HttpResponseRedirect('/compare_orgs/' + str(job.random_id) + '/?api=' + job.api_choice)
	
	# Build HTML here - improves page load performance
	html_rows = ''.join(list(job.sorted_component_list().values_list('row_html', flat=True)))

	return render_to_response('compare_results.html', RequestContext(request, {
		'org_left_username': job.sorted_orgs()[0].username, 
		'org_right_username': job.sorted_orgs()[1].username, 
		'html_rows': html_rows,
		'job': job
	}))


# Re-run the job, user the user doens't have to re-authenticate
def rerunjob(request, job_id):

	# Query for job
	job = get_object_or_404(Job, random_id = job_id)

	# Set the status to force re-run
	job.status = 'Not Started'

	# Delete component unique list
	job.sorted_component_list().delete()

	# Delete component types and components
	for component_types in job.sorted_orgs():
		component_types.sorted_component_types().delete()

	# Save job changes
	job.save()

	# Redirect user and re-run the job
	return HttpResponseRedirect('/compare_orgs/' + str(job.random_id) + '/?api=' + job.api_choice)


# AJAX endpoint for page to constantly check if job is finished
def check_file_status(request, job_id):

	# Query for job
	job = get_object_or_404(Job, random_id = job_id)

	# If job is finished
	if job.zip_file:

		response_data = {
			'status': 'Finished',
			'url': job.zip_file.url,
			'error': ''
		}

	# Else check for any errors
	elif job.zip_file_error:

		response_data = {
			'status': 'Error',
			'url': '',
			'error': job.zip_file_error
		}

	else:

		response_data = {
			'status': 'Running',
			'url': '',
			'error': ''
		}

	return HttpResponse(json.dumps(response_data), content_type = 'application/json')


# AJAX endpoint for getting the metadata of a component
def get_metadata(request, component_id):
	component = get_object_or_404(Component, pk = component_id)
	return HttpResponse(component.content)


# AJAX endpoint for getting the diff HTML of a component
def get_diffhtml(request, component_id):
	component = get_object_or_404(ComponentListUnique, pk = component_id)
	return HttpResponse(component.diff_html)
