from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from ripozo.dispatch.adapters.base import AdapterBase
from ripozo.utilities import titlize_endpoint
from ripozo.viewsets.resource_base import create_url
from ripozo.viewsets import status_constants
import json
import six

_content_type = 'application/vnd.siren+json'


class SirenAdapter(AdapterBase):
    """
    An adapter that formats the response in the SIREN format.
    A description of a SIREN format can be found here:
    `SIREN specification <https://github.com/kevinswiber/siren>`_
    """
    formats = ['siren', _content_type]

    @property
    def formatted_body(self):
        """
        Gets the formatted body of the response in unicode form.

        :return: The siren formatted response body
        :rtype: unicode
        """
        if self.resource.status == status_constants.DELETED:
            return ''  # TODO write test to prevent regressions here

        links = [dict(rel=['self'], href=self.resource.url)]

        entities, updated_properties = self.get_entities_and_remove_related_properties()
        response = dict(properties=updated_properties, actions=self._actions,
                        links=links, entities=entities)

        # need to do this separately since class is a reserved keyword
        response['class'] = [self.resource.resource_name]
        return json.dumps(response)

    @property
    def _actions(self):
        """
        Gets the list of actions in an appropriately SIREN format

        :return: The list of actions
        :rtype: list
        """
        actions = []
        for endpoint, options in six.iteritems(self.resource.endpoint_dictionary):
            options = options[0]
            all_methods = options.get('methods', [])
            if len(all_methods) == 0:
                meth = 'GET'
            else:
                meth = all_methods[0]
            base_route = options.get('route', self.resource.base_url)
            route = create_url(base_route, **self.resource.properties)
            actn = dict(name=endpoint, title=titlize_endpoint(endpoint), method=meth, href=route)
            actions.append(actn)
        return actions

    def get_entities_and_remove_related_properties(self):
        """
        Gets a list of related entities in an appropriate SIREN format

        :return: A list of entities
        :rtype: list
        """
        entities = []
        parent_properties = self.resource.properties.copy()
        for field_name, relationship in six.iteritems(self.resource.relationships):
            ent = {'class': [relationship.relation.resource_name]}
            related_resource = relationship.construct_resource(self.resource.properties)
            if not relationship.embedded:
                ent['href'] = related_resource.url
                updated_properties = relationship.remove_child_resource_properties(parent_properties)
            else:
                ent['properties'] = related_resource.properties
                ent['links'] = dict(rel=['self'], href=related_resource.url)
            entities.append(ent)
        return entities, parent_properties


    @property
    def extra_headers(self):
        """
        The headers that should be appended to the response

        :return: a list of the headers to be set on the
            response
        :rtype: list
        """
        return [{'Content-Type': _content_type}]