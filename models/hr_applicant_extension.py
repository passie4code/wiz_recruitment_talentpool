from odoo import models, fields, api
from datetime import date
    
class Applicant(models.Model):
    _inherit = 'hr.applicant'
    
    # nieuwe velden en uitbreidingen
    talent_id = fields.Many2one('wiz.recruitment.talentpool.talent', string="Talent")
    education_ids = fields.One2many('recruitment.education', 'applicant_id')
    experience_ids = fields.One2many('recruitment.experience', 'applicant_id')
    skill_ids = fields.One2many('recruitment.skill', 'applicant_id')

    def action_convert_to_talent(self):
        Talent = self.env['wiz.recruitment.talentpool.talent'].sudo()
        for applicant in self:
            if applicant.talent_id:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Talent al gekoppeld",
                        'message': f"Sollicitant '{applicant.name}' is al gekoppeld aan een Talent-profiel.",
                        'type': 'warning',
                        'sticky': True,
                    }
                }

            existing = Talent.search([
                '|',
                ('email', '=', applicant.email_from),
                ('linkedin_profile', '=', applicant.linkedin_profile)
            ], limit=1)

            if existing:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Talent bestaat al",
                        'message': f"Talent '{existing.name}' bestaat al in de Talent Pool.",
                        'type': 'warning',
                        'sticky': True,
                    }
                }

            new_talent = Talent.create({
                'name': applicant.partner_name or applicant.name,
                'email': applicant.email_from,
                'phone': applicant.phone,
                'linkedin_profile': applicant.linkedin_profile,
                'notes': applicant.description,
                'creation_date': date.today(),
                'last_update_date': date.today(),
            })

            # Bijlagen koppelen
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', applicant.id)
            ])
            new_talent.attachment_ids = [(4, att.id) for att in attachments]

            applicant.talent_id = new_talent.id

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Talent aangemaakt",
                    'message': f"Sollicitant '{applicant.name}' is succesvol omgezet naar Talent.",
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_bulk_convert_to_talent(self):
        Talent = self.env['wiz.recruitment.talentpool.talent'].sudo()
        created = 0
        skipped = 0

        for applicant in self:
            if applicant.talent_id:
                skipped += 1
                continue

            existing = Talent.search([
                ('email', '=', applicant.email_from)
            ], limit=1)

            if existing:
                applicant.talent_id = existing.id
                skipped += 1
                continue

            new_talent = Talent.create({
                'name': applicant.partner_name or applicant.name,
                'email': applicant.email_from,
                'linkedin_profile': applicant.linkedin_profile,
                'creation_date': date.today(),
                'last_update_date': date.today(),
                'notes': applicant.description,
            })

            applicant.talent_id = new_talent.id
            created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Bulkconversie voltooid",
                'message': f"{created} talenten aangemaakt, {skipped} overgeslagen.",
                'type': 'success',
                'sticky': False,
            }
        }
    def copy_talent_data_to_applicant(self, talent):
        for record in talent.education_ids:
            self.env['recruitment.education'].create({
                'name': record.name,
                'institute': record.institute,
                'start_date': record.start_date,
                'end_date': record.end_date,
                'applicant_id': self.id,
            })
        for record in talent.experience_ids:
            self.env['recruitment.experience'].create({
                'name': record.name,
                'company': record.company,
                'start_date': record.start_date,
                'end_date': record.end_date,
                'description': record.description,
                'applicant_id': self.id,
            })
        for record in talent.skill_ids:
            self.env['recruitment.skill'].create({
                'name': record.name,
                'level': record.level,
                'applicant_id': self.id,
            })
