import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class TalentPortal(http.Controller):

    # Overzicht van sollicitaties
    @http.route('/my/applications', type='http', auth='user', website=True)
    def portal_applications(self):
        user = request.env.user

        # Zoek het talentprofiel van de ingelogde gebruiker
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)

        # Zoek sollicitaties die gekoppeld zijn aan dat talentprofiel
        applications = request.env['hr.applicant'].sudo().search([
            ('talent_id', '=', talent.id),
            ('active', '=', True)
        ]) if talent else []

        _logger.info("Aantal sollicitaties gevonden: %s", len(applications))
        
        return request.render('wiz_recruitment_talentpool.portal_applications', {
            'applications': applications,
        })

    # GET: Toon formulier voor sollicitatie via portaal
    @http.route('/my/apply', type='http', auth='user', website=True)
    def portal_apply_form(self):
        jobs = request.env['hr.job'].sudo().search([('website_published', '=', True)])
        _logger.info("Sollicitatieformulier geladen met %s functies", len(jobs))
        return request.render('wiz_recruitment_talentpool.portal_apply_form', {
            'jobs': jobs,
        })

    # POST: Verwerk het sollicitatieformulier in de portaal
    @http.route('/my/apply/submit', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_apply_submit(self, **post):
        _logger.info("POST ontvangen: %s", post)
        user = request.env.user
        job_id = int(post.get('job_id', 0))
        _logger.info("Gekozen job_id: %s", job_id)

        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        _logger.info("Gevonden talentprofiel: %s", talent.name if talent else "Geen")

        if not talent or not job_id:
            _logger.warning("Geen talentprofiel of job geselecteerd — redirect naar formulier")
            return request.redirect('/my/apply')
        
        # Maak nieuwe applicant aan
        applicant = request.env['hr.applicant'].sudo().create({
            'name': talent.name,
            'partner_id': user.partner_id.id,
            'talent_id': talent.id,
            'job_id': job_id,
        })
        _logger.info("Applicant aangemaakt: %s (ID %s)", applicant.name, applicant.id)

        # Kopieer talentdata
        if hasattr(applicant, 'copy_talent_data_to_applicant'):
            try:
                applicant.copy_talent_data_to_applicant(talent)
                _logger.info("Talentdata succesvol gekopieerd naar applicant")
            except Exception as e:
                _logger.error("Fout bij kopiëren van talentdata: %s", str(e))

        # Redirect naar sollicitatie-overzicht
        return request.redirect('/my/applications')
    
    # Toon de Talent-persoonsgegevens en wensen in de portaal
    @http.route('/my/talent', type='http', auth='user', website=True)
    def portal_talent_profile(self):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)

        if not talent:
            return request.render('wiz_recruitment_talentpool.portal_talent_profile', {
                'talent': False,
                'applications': [],
            })

        applications = request.env['hr.applicant'].sudo().search([
            ('talent_id', '=', talent.id),
            ('active', '=', True)
        ])

        return request.render('wiz_recruitment_talentpool.portal_talent_profile', {
            'talent': talent,
            'applications': applications,
            'educations': talent.education_ids,
            'experiences': talent.experience_ids,
            'skills': talent.skill_ids,
        })

    @http.route('/my/talent/update', type='http', auth='user', methods=['POST'], website=True)
    def portal_talent_update(self, **post):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        if talent:
            talent.write({
                'searching_for': post.get('searching_for'),
                'not_wanted': post.get('not_wanted'),
                'notes': post.get('notes'),
                'last_update_date': fields.Date.today(),
            })
        return request.redirect('/my/talent')
    
    # -------------------------------------
    # ---  EDUCATIE - PORTAALLOGICA     ---
    # -------------------------------------
    # Toon de educatie en scholing in de portaal
    @http.route('/my/education', type='http', auth='user', website=True)
    def portal_education(self):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        educations = talent.education_ids if talent else []
        return request.render('wiz_recruitment_talentpool.portal_education', {
            'talent': talent,
            'educations': educations,
        })

    @http.route('/my/education/add', type='http', auth='user', website=True)
    def portal_education_add(self):
        return request.render('wiz_recruitment_talentpool.portal_education_add', {})

    @http.route('/my/education/add/submit', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_education_submit(self, **post):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        if talent:
            request.env['recruitment.education'].sudo().create({
                'name': post.get('name'),
                'institute': post.get('institute'),
                'start_date': post.get('start_date'),
                'end_date': post.get('end_date'),
                'talent_id': talent.id,
            })
        return request.redirect('/my/education')

    # -------------------------------------
    # ---  EXPERIENCE - PORTAALLOGICA   ---
    # -------------------------------------
    # Toon de werkervaring en vorige werkgevers in de portaal
    @http.route('/my/experience', type='http', auth='user', website=True)
    def portal_experience(self):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        experiences = talent.experience_ids if talent else []
        return request.render('wiz_recruitment_talentpool.portal_experience', {
            'talent': talent,
            'experiences': experiences,
        })

    @http.route('/my/experience/add', type='http', auth='user', website=True)
    def portal_experience_add(self):
        return request.render('wiz_recruitment_talentpool.portal_experience_add', {})

    @http.route('/my/experience/add/submit', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_experience_submit(self, **post):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        if talent:
            request.env['recruitment.experience'].sudo().create({
                'name': post.get('name'),
                'company': post.get('company'),
                'start_date': post.get('start_date'),
                'end_date': post.get('end_date'),
                'description': post.get('description'),
                'talent_id': talent.id,
            })
        return request.redirect('/my/experience')
    
    @http.route('/my/experience/edit', type='http', auth='user', website=True)
    def portal_experience_edit(self):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        experiences = talent.experience_ids if talent else []
        return request.render('wiz_recruitment_talentpool.portal_experience_edit', {
            'experiences': experiences,
        })

    @http.route('/my/experience/update', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_experience_update(self, **post):
        ids = request.httprequest.form.getlist('exp_ids')
        for exp_id in ids:
            exp = request.env['recruitment.experience'].sudo().browse(int(exp_id))
            exp.write({
                'name': post.get(f'name_{exp_id}'),
                'company': post.get(f'company_{exp_id}'),
                'start_date': post.get(f'start_{exp_id}'),
                'end_date': post.get(f'end_{exp_id}'),
                'description': post.get(f'desc_{exp_id}'),
            })
        return request.redirect('/my/experience')

    # -------------------------------------
    # ---    SKILLS - PORTAALLOGICA     ---
    # -------------------------------------
    # Toon de Skill en ervaring in de portaal
    @http.route('/my/skills', type='http', auth='user', website=True)
    def portal_skills(self):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        skills = talent.skill_ids if talent else []
        return request.render('wiz_recruitment_talentpool.portal_skills', {
            'talent': talent,
        })
    
    @http.route('/my/skills/add', type='http', auth='user', website=True)
    def portal_skills_add(self):
        return request.render('wiz_recruitment_talentpool.portal_skills_add', {})

    @http.route('/my/skills/add/submit', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_skills_submit(self, **post):
        user = request.env.user
        talent = request.env['wiz.recruitment.talentpool.talent'].sudo().search([
            ('portal_user_id', '=', user.id)
        ], limit=1)
        if talent:
            request.env['recruitment.skill'].sudo().create({
                'name': post.get('name'),
                'level': post.get('level'),
                'talent_id': talent.id,
            })
        return request.redirect('/my/skills')
