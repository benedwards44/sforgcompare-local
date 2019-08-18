from django import forms
from suds.client import Client
from django.conf import settings

class JobForm(forms.Form):
	org_one_type = forms.ChoiceField(choices=(('Production', 'Production'),('Sandbox','Sandbox')))
	org_one_username = forms.CharField()
	org_one_password = forms.CharField()
	org_one_session_id = forms.CharField(required=False)
	org_one_metadata_url = forms.CharField(required=False)
	org_one_org_id = forms.CharField(required=False)
	org_one_org_name = forms.CharField(required=False)
	org_two_type = forms.ChoiceField(choices=(('Production', 'Production'),('Sandbox','Sandbox')))
	org_two_username = forms.CharField()
	org_two_password = forms.CharField()
	org_two_session_id = forms.CharField(required=False)
	org_two_metadata_url = forms.CharField(required=False)
	org_two_org_id = forms.CharField(required=False)
	org_two_org_name = forms.CharField(required=False)
	api_choice = forms.ChoiceField(choices=(('metadata', 'Metadata API'),('tooling','Tooling API')))
	contextual_diff = forms.BooleanField(required=False, initial=True)

	def clean(self):

		cleaned_data = super(JobForm, self).clean()

		# Attempt login of Org One
		org_one_login_result = self.login_successful(
			cleaned_data['org_one_type'],
			cleaned_data['org_one_username'],
			cleaned_data['org_one_password']
		)

		if org_one_login_result and org_one_login_result.sessionId:
			cleaned_data['org_one_session_id'] = org_one_login_result.sessionId
			cleaned_data['org_one_metadata_url'] = org_one_login_result.metadataServerUrl
			cleaned_data['org_one_org_id'] = org_one_login_result.userInfo.organizationId
			cleaned_data['org_one_org_name'] = org_one_login_result.userInfo.organizationName
		else:
			raise forms.ValidationError('Error logging into Org One. Please check your username and password and try again.')
		

		# Attempt login of Org One
		org_two_login_result = self.login_successful(
			cleaned_data['org_two_type'],
			cleaned_data['org_two_username'],
			cleaned_data['org_two_password']
		)

		if org_two_login_result and org_two_login_result.sessionId:
			cleaned_data['org_two_session_id'] = org_two_login_result.sessionId
			cleaned_data['org_two_metadata_url'] = org_two_login_result.metadataServerUrl
			cleaned_data['org_two_org_id'] = org_two_login_result.userInfo.organizationId
			cleaned_data['org_two_org_name'] = org_two_login_result.userInfo.organizationName
		else:
			raise forms.ValidationError('Error logging into Org Two. Please check your username and password and try again.')

		return cleaned_data

	def login_successful(self, org_type, username, password):

		# Load WSDL and login
		wsdl = settings.SALESFORCE_PARTNER_PRODUCTION_WSDL if org_type == 'Production' else settings.SALESFORCE_PARTNER_SANDBOX_WSDL
		client = Client(wsdl)

		try:
			login_result = client.service.login(username, password)
			return login_result
		except:
			return None

		