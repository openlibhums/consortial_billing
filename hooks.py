from django.urls import reverse


def admin_hook(context):
    return '''
           <li>
             <a href="{url}">
               <i class="fa fa-money"></i>
               Consortial Billing
             </a>
           </li>
           '''.format(url=reverse('supporters_manager'))
