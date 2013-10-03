MONITOR = ('split', {'direction': 'vertical', 'ratios': ['10%', '90%']},
    ('split', {'direction': 'horizontal', 'ratios': ['75%', '25%']},
        ('text', {'text': 'status monitor'}),
        ('clock', {}),
    ),
    ('split', {'direction': 'horizontal', 'ratios': ['40%', '35%', '25%']},
        ('sentry', {'count': 15}),
        ('travis', {'username': '', 'token': ''}),
        ('split', {'direction': 'vertical'},
            ('github', {}),
            ('statuscake', {})
        ),
    )
)


AGGREGATORS = (
    ('sentry', {'url': '', 'username': '', 'password': ''}),
    ('travis', {'username': '', 'token': ''}),
    ('github', {'token': '', 'company': ''}),
    ('statuscake', {'token': '', 'username': ''})
)
