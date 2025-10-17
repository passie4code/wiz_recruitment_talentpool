from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, date

class TalentEducation(models.Model):
    _name = 'recruitment.education'
    _description = 'Opleiding'

    name = fields.Char("Opleiding")
    institute = fields.Char("Instituut")
    start_date = fields.Date("Startdatum")
    end_date = fields.Date("Einddatum")
    talent_id = fields.Many2one('wiz.recruitment.talentpool.talent', string="Talent")
    applicant_id = fields.Many2one('hr.applicant', string="Sollicitatie")

class TalentExperience(models.Model):
    _name = 'recruitment.experience'
    _description = 'Werkervaring'

    name = fields.Char("Functie")
    company = fields.Char("Bedrijf")
    start_date = fields.Date("Startdatum")
    end_date = fields.Date("Einddatum")
    description = fields.Text("Beschrijving")
    talent_id = fields.Many2one('wiz.recruitment.talentpool.talent')
    applicant_id = fields.Many2one('hr.applicant')

class TalentSkill(models.Model):
    _name = 'recruitment.skill'
    _description = 'Skill'

    name = fields.Char("Skill")
    level = fields.Selection([('beginner', 'Beginner'), ('intermediate', 'Gemiddeld'), ('expert', 'Expert')])
    talent_id = fields.Many2one('wiz.recruitment.talentpool.talent')
    applicant_id = fields.Many2one('hr.applicant')

class Talent(models.Model):
    _name = 'wiz.recruitment.talentpool.talent'
    _description = 'Talent Pool Entry'

    # Basisgegevens
    name = fields.Char(required=True)
    email = fields.Char(required=True)
    phone = fields.Char(string="Telefoonnummer")
    linkedin_profile = fields.Char(string="LinkedIn-profiel")
    cv_attachment_id = fields.Many2one('ir.attachment', string="CV-bestand")
    creation_date = fields.Date(default=lambda self: date.today())
    last_update_date = fields.Date()

    # Profielinhoud
    education_ids = fields.One2many('recruitment.education', 'talent_id')
    experience_ids = fields.One2many('recruitment.experience', 'talent_id')
    skill_ids = fields.One2many('recruitment.skill', 'talent_id')

    # Wensenlijst
    searching_for = fields.Text(string="Ik ben op zoek naar:")
    not_wanted = fields.Text(string="Wat ik niet wens:")
    notes = fields.Text(string="Overige opmerkingen")
 
    # Bijlagen
    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'wiz.recruitment.talentpool.talent')],
        string="Bijlagen"
    )

    # Verwijderingslogica
    marked_for_deletion = fields.Boolean(string="Markeer voor verwijdering")
    deletion_reason = fields.Text(string="Reden voor verwijdering")
    marked_by_user = fields.Many2one('res.users', string="Gemarkeerd door")

    # Portaalgebruiker
    portal_user_id = fields.Many2one('res.users', string="Portaalgebruiker")

    # Historiek
    application_history_ids = fields.One2many(
        'hr.applicant', 'talent_id', string="Sollicitatiehistoriek"
    )

    # Tagging
    inactive_tag = fields.Boolean(string="1 jaar geen wijziging", compute="_compute_inactive_tag")

    @api.depends('last_update_date')
    def _compute_inactive_tag(self):
        for record in self:
            if record.last_update_date:
                record.inactive_tag = (date.today() - record.last_update_date) > timedelta(days=365)
            else:
                record.inactive_tag = False

    # def action_reapply(self):
    #    for record in self:
    #        self.env['hr.applicant'].create({
    #            'name': record.name,
    #            'email_from': record.email,
    #            'partner_name': record.name,
    #            'phone': record.phone,
    #            'description': 'Herplaatst vanuit Talent Pool',
    #            'talent_id': record.id,
    #        })

    #-------------------------------------------------------------------------
    # Acties
    #-------------------------------------------------------------------------


    def action_reapply(self):
        for talent in self:
            applicant = self.env['hr.applicant'].create({
                'name': talent.name,
                'partner_id': talent.portal_user_id.partner_id.id,
                'talent_id': talent.id,
            })
            applicant.copy_talent_data_to_applicant(talent)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.applicant',
                'view_mode': 'form',
                'res_id': applicant.id,
                'target': 'current',
            }
    
    def action_create_portal_user(self):
        for record in self:
            if record.portal_user_id:
                raise UserError("Portaalgebruiker bestaat al.")
            partner = self.env['res.partner'].create({
                'name': record.name,
                'email': record.email,
                'phone': record.phone,
            })
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email,
                'email': record.email,
                'partner_id': partner.id,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            })
            record.portal_user_id = user.id

    def action_reset_portal_user(self):
        for record in self:
            if not record.portal_user_id:
                raise UserError("Geen gekoppelde portaalgebruiker.")
            record.portal_user_id.action_reset_password()

    def action_open_linkedin(self):
        for record in self:
            if not record.linkedin_profile:
                raise UserError("Geen LinkedIn-profiel beschikbaar.")
            return {
                'type': 'ir.actions.act_url',
                'url': record.linkedin_profile,
                'target': 'new',
            }
