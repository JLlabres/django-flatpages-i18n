from django import template
from django.conf import settings

from flatpages_i18n.models import FlatPage_i18n

register = template.Library()


class FlatpageNode(template.Node):
    def __init__(self, context_name, starts_with=None, contains=None,
                 excludes=None, user=None):
        self.context_name = context_name
        if starts_with:
            self.starts_with = template.Variable(starts_with)
        else:
            self.starts_with = None

        if contains:
            self.contains = template.Variable(contains)
        else:
            self.contains = None

        if excludes:
            self.excludes = template.Variable(excludes)
        else:
            self.excludes = None

        if user:
            self.user = template.Variable(user)
        else:
            self.user = None

    def render(self, context):
        flatpages = FlatPage_i18n.objects.filter(
            sites__id=settings.SITE_ID,
        ).order_by('weight')

        # If a prefix was specified, add a filter
        if self.starts_with:
            flatpages = flatpages.filter(
                url__startswith=self.starts_with.resolve(context))

        # If a string to contain was specified, add a filter
        if self.contains:
            flatpages = flatpages.filter(
                url__contains=self.contains.resolve(context))

    # If a string to exclude was specified, add a filter
        if self.excludes:
            flatpages = flatpages.exclude(
                url__contains=self.excludes.resolve(context))

        # If the provided user is not authenticated, or no user
        # was provided, filter the list to only public flatpages.
        if self.user:
            user = self.user.resolve(context)
            if not user.is_authenticated():
                flatpages = flatpages.filter(registration_required=False)
        else:
            flatpages = flatpages.filter(registration_required=False)

        context[self.context_name] = flatpages
        return ''


@register.tag
def get_flatpages_i18n(parser, token):
    """
    Retrieves all flatpage objects available for the current site and
    visible to the specific user (or visible to all users if no user is
    specified). Populates the template context with them in a variable
    whose name is defined by the ``as`` clause.

    An optional ``for`` clause can be used to control the user whose
    permissions are to be used in determining which flatpages are visible.

    An optional argument, ``starts_with``, can be applied to limit the
    returned flatpages to those beginning with a particular base URL.
    This argument can be passed as a variable or a string, as it resolves
    from the template context.

    Syntax::

        {% get_flatpages ['url_starts_with'] [for user] as context_name %}

    Example usage::

        {% get_flatpages as flatpages %}
        {% get_flatpages for someuser as flatpages %}
        {% get_flatpages '/about/' as about_pages %}
        {% get_flatpages prefix as about_pages %}
        {% get_flatpages '/about/' for someuser as about_pages %}
        {% get_flatpages containing '/sk/' as my_pages %}
        {% get_flatpages excluding '/sk/' as my_pages %}
    """
    bits = token.split_contents()
    syntax_message = ("%(tag_name)s expects a syntax of %(tag_name)s "
                      "['url_starts_with'] [for user] as context_name" %
                      dict(tag_name=bits[0]))

    # Must have at 3-6 bits in the tag
    if len(bits) >= 3 and len(bits) <= 8:
        containing = None
        excluding = None

        # If there's an even number of bits, there's no prefix
        if len(bits) % 2 == 0:
            prefix = bits[1]
        else:
            prefix = None
        if bits[1] == "containing":
            containing = bits[2]
        else:
            if bits[1] == "excluding":
                excluding = bits[2]

        # The very last bit must be the context name
        if bits[-2] != 'as':
            raise template.TemplateSyntaxError(syntax_message)
        context_name = bits[-1]

        # If there are 5 or 6 bits, there is a user defined
        user = None
#        if len(bits) >= 5:
            #if bits[-4] != 'for':
                #raise template.TemplateSyntaxError(syntax_message)
        if bits[-4] == 'for':
            user = bits[-3]

        return FlatpageNode(
            context_name, starts_with=prefix, contains=containing,
            excludes=excluding, user=user)
    else:
        raise template.TemplateSyntaxError(syntax_message)
