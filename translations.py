
from flask import session, request
import json

class Translations:
    def __init__(self):
        self.languages = {
            'so': {
                'app_name': 'Dadaal App',
                'welcome': 'Ku soo dhawow',
                'home': 'Hore',
                'login': 'Gal',
                'register': 'Diiwaan geli',
                'dashboard': 'Dashboard',
                'payment': 'Lacag shubo',
                'gifts': 'Hadiyado',
                'ads': 'Xayeysiisyo',
                'referral': 'Invite Friends',
                'premium': 'Premium',
                'affiliate': 'Affiliate',
                'earnings': 'Dakhli',
                'profile': 'Profile',
                'logout': 'Ka bax',
                'email': 'Email',
                'password': 'Password',
                'name': 'Magaca',
                'phone': 'Telefoon',
                'confirm_password': 'Xaqiiji password-ka',
                'forgot_password': 'Password ma xusuusanaysid?',
                'reset_password': 'Bedel password-ka',
                'verify_email': 'Xaqiiji email-ka',
                'contact': 'La xiriir',
                'about': 'Naga',
                'terms': 'Shuruudaha',
                'privacy': 'Sirta',
                'hero_title': '💰 Ku Bilaw Lacag Samynta Maanta!',
                'hero_subtitle': 'Nidaamka ugu fiican ee lacag samynta online-ka ah',
                'total_earnings': 'Lacagta la helay',
                'users': 'Users',
                'support': 'Support',
                'featured_services': '🚀 Adeegyada Ugu Waaweyn',
                'referral_program': 'Referral Program',
                'referral_desc': 'Hel $5 qof walba oo aad soo dirtid',
                'premium_account': 'Premium Account',
                'premium_desc': '5x lacag badan oo bonuses ah',
                'affiliate_marketing': 'Affiliate Marketing',
                'affiliate_desc': '20% commission dhammaan sales-ka',
                'start_now': 'Bilaw hadda',
                'upgrade': 'Upgrade',
                'join_now': 'Join Now',
                'quick_actions': '⚡ Quick Actions',
                'latest_updates': '📢 Warar Cusub',
                'copyright': '© 2025 Dadaal App. Dhamaan xuquuqda way dhowran yihiin.',
                'made_with_love': 'Made with ❤️ for Somali Entrepreneurs'
            },
            'en': {
                'app_name': 'Dadaal App',
                'welcome': 'Welcome',
                'home': 'Home',
                'login': 'Login',
                'register': 'Register',
                'dashboard': 'Dashboard',
                'payment': 'Payment',
                'gifts': 'Gifts',
                'ads': 'Ads',
                'referral': 'Referral',
                'premium': 'Premium',
                'affiliate': 'Affiliate',
                'earnings': 'Earnings',
                'profile': 'Profile',
                'logout': 'Logout',
                'email': 'Email',
                'password': 'Password',
                'name': 'Name',
                'phone': 'Phone',
                'confirm_password': 'Confirm Password',
                'forgot_password': 'Forgot Password?',
                'reset_password': 'Reset Password',
                'verify_email': 'Verify Email',
                'contact': 'Contact',
                'about': 'About',
                'terms': 'Terms',
                'privacy': 'Privacy',
                'hero_title': '💰 Start Earning Money Today!',
                'hero_subtitle': 'The best online money-making platform',
                'total_earnings': 'Total Earnings',
                'users': 'Users',
                'support': 'Support',
                'featured_services': '🚀 Featured Services',
                'referral_program': 'Referral Program',
                'referral_desc': 'Get $5 for every person you refer',
                'premium_account': 'Premium Account',
                'premium_desc': '5x more money and bonuses',
                'affiliate_marketing': 'Affiliate Marketing',
                'affiliate_desc': '20% commission on all sales',
                'start_now': 'Start Now',
                'upgrade': 'Upgrade',
                'join_now': 'Join Now',
                'quick_actions': '⚡ Quick Actions',
                'latest_updates': '📢 Latest Updates',
                'copyright': '© 2025 Dadaal App. All rights reserved.',
                'made_with_love': 'Made with ❤️ for Entrepreneurs'
            },
            'ar': {
                'app_name': 'تطبيق دادال',
                'welcome': 'مرحبا',
                'home': 'الرئيسية',
                'login': 'تسجيل الدخول',
                'register': 'التسجيل',
                'dashboard': 'لوحة التحكم',
                'payment': 'الدفع',
                'gifts': 'الهدايا',
                'ads': 'الإعلانات',
                'referral': 'الإحالة',
                'premium': 'المميز',
                'affiliate': 'التسويق بالعمولة',
                'earnings': 'الأرباح',
                'profile': 'الملف الشخصي',
                'logout': 'تسجيل الخروج',
                'email': 'البريد الإلكتروني',
                'password': 'كلمة المرور',
                'name': 'الاسم',
                'phone': 'الهاتف',
                'confirm_password': 'تأكيد كلمة المرور',
                'forgot_password': 'نسيت كلمة المرور؟',
                'reset_password': 'إعادة تعيين كلمة المرور',
                'verify_email': 'تأكيد البريد الإلكتروني',
                'contact': 'اتصل بنا',
                'about': 'عنا',
                'terms': 'الشروط',
                'privacy': 'الخصوصية',
                'hero_title': '💰 ابدأ في كسب المال اليوم!',
                'hero_subtitle': 'أفضل منصة لكسب المال عبر الإنترنت',
                'total_earnings': 'إجمالي الأرباح',
                'users': 'المستخدمون',
                'support': 'الدعم',
                'featured_services': '🚀 الخدمات المميزة',
                'referral_program': 'برنامج الإحالة',
                'referral_desc': 'احصل على $5 لكل شخص تحيله',
                'premium_account': 'الحساب المميز',
                'premium_desc': '5 أضعاف المال والمكافآت',
                'affiliate_marketing': 'التسويق بالعمولة',
                'affiliate_desc': '20% عمولة على جميع المبيعات',
                'start_now': 'ابدأ الآن',
                'upgrade': 'ترقية',
                'join_now': 'انضم الآن',
                'quick_actions': '⚡ إجراءات سريعة',
                'latest_updates': '📢 آخر التحديثات',
                'copyright': '© 2025 تطبيق دادال. جميع الحقوق محفوظة.',
                'made_with_love': 'صنع بـ ❤️ لرواد الأعمال'
            },
            'fr': {
                'app_name': 'Dadaal App',
                'welcome': 'Bienvenue',
                'home': 'Accueil',
                'login': 'Se connecter',
                'register': "S'inscrire",
                'dashboard': 'Tableau de bord',
                'payment': 'Paiement',
                'gifts': 'Cadeaux',
                'ads': 'Publicités',
                'referral': 'Parrainage',
                'premium': 'Premium',
                'affiliate': 'Affiliation',
                'earnings': 'Gains',
                'profile': 'Profil',
                'logout': 'Se déconnecter',
                'email': 'Email',
                'password': 'Mot de passe',
                'name': 'Nom',
                'phone': 'Téléphone',
                'confirm_password': 'Confirmer le mot de passe',
                'forgot_password': 'Mot de passe oublié?',
                'reset_password': 'Réinitialiser le mot de passe',
                'verify_email': "Vérifier l'email",
                'contact': 'Contact',
                'about': 'À propos',
                'terms': 'Conditions',
                'privacy': 'Confidentialité',
                'hero_title': "💰 Commencez à gagner de l'argent aujourd'hui!",
                'hero_subtitle': 'La meilleure plateforme de gains en ligne',
                'total_earnings': 'Gains totaux',
                'users': 'Utilisateurs',
                'support': 'Support',
                'featured_services': '🚀 Services en vedette',
                'referral_program': 'Programme de parrainage',
                'referral_desc': 'Obtenez 5$ pour chaque personne que vous parrainez',
                'premium_account': 'Compte Premium',
                'premium_desc': "5x plus d'argent et de bonus",
                'affiliate_marketing': 'Marketing d\'affiliation',
                'affiliate_desc': '20% de commission sur toutes les ventes',
                'start_now': 'Commencer maintenant',
                'upgrade': 'Mettre à niveau',
                'join_now': 'Rejoindre maintenant',
                'quick_actions': '⚡ Actions rapides',
                'latest_updates': '📢 Dernières mises à jour',
                'copyright': '© 2025 Dadaal App. Tous droits réservés.',
                'made_with_love': 'Fait avec ❤️ pour les entrepreneurs'
            }
        }
    
    def get_language(self):
        # Get language from session, URL parameter, or browser preference
        if 'language' in session:
            return session['language']
        
        lang = request.args.get('lang')
        if lang and lang in self.languages:
            session['language'] = lang
            return lang
        
        # Default to Somali
        return 'so'
    
    def set_language(self, lang):
        if lang in self.languages:
            session['language'] = lang
            return True
        return False
    
    def translate(self, key, lang=None):
        if not lang:
            lang = self.get_language()
        
        if lang in self.languages and key in self.languages[lang]:
            return self.languages[lang][key]
        
        # Fallback to Somali
        if key in self.languages['so']:
            return self.languages['so'][key]
        
        return key  # Return key if no translation found

# Global translator instance
translator = Translations()

def t(key, lang=None):
    """Translation helper function"""
    return translator.translate(key, lang)
