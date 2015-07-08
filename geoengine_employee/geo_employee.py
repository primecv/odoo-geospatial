# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2011-2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api
import logging
from openerp import exceptions
from openerp.tools.translate import _

from openerp.addons.base_geoengine import geo_model
from openerp.addons.base_geoengine import fields

from openerp.osv import osv
from openerp import fields as oe_fields


try:
    import requests
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('requests is not available in the sys path')

_logger = logging.getLogger(__name__)


class hr_employee(geo_model.GeoModel, osv.osv):
    _inherit = "hr.employee"


    @api.one
    def geocode_address(self):
        """Get the latitude and longitude by requesting "mapquestapi"
        see http://open.mapquestapi.com/geocoding/
        """
        url = 'http://nominatim.openstreetmap.org/search'
        pay_load = {
            'limit': 1,
            'format': 'json',
            'postalCode': self.zip or '',
            'city': self.city or '',
            'country': self.country and self.country.name or '',
            'countryCodes': self.country and self.country.code or ''}

        request_result = requests.get(url, params=pay_load)
        try:
            request_result.raise_for_status()
        except Exception as e:
            _logger.exception('Geocoding error')
            raise exceptions.Warning(_(
                'Geocoding error. \n %s') % e.message)
        vals = request_result.json()
        vals = vals and vals[0] or {}
        self.write({
            'employee_latitude': vals.get('lat'),
            'employee_longitude': vals.get('lon'),
            })

    @api.one
    def geo_localize(self):
        self.geocode_address()
        return True

    @api.one
    @api.depends('employee_latitude', 'employee_longitude')
    def _get_geo_point(self):
        if not self.employee_latitude or not self.employee_longitude:
            self.geo_point = False
        else:
            self.geo_point = fields.GeoPoint.from_latlon(
                self.env.cr, self.employee_latitude, self.employee_longitude)

    geo_point = fields.GeoPoint(string='Addresses Coordinate', readonly=True, store=True, compute='_get_geo_point')
    city = oe_fields.Char(related='address_home_id.city', string='City', store=True)
    zip = oe_fields.Char(related='address_home_id.zip', string='Zip', store=True)
    country = oe_fields.Many2one('res.country', string='Country', related='address_home_id.country_id', store=True)
    employee_latitude = oe_fields.Float(related='address_home_id.partner_latitude', string='Latitude', store=True)
    employee_longitude = oe_fields.Float(related='address_home_id.partner_longitude', string='Longitude', store=True)

