"""Data-only draft review delegates exclusively to the actual Rise initializer."""
import copy
import unittest
from test_settlement import choices
import world_draft as api


class WorldDraftTests(unittest.TestCase):
    def draft(self):
        return {'schema_version':api.SCHEMA_VERSION,'draft_id':'synthetic-world','classification':'fictional',
                'profile_id':'rise-r00','choices':choices()}

    def test_preview_and_explicit_initialization_match_existing_review(self):
        draft=self.draft();before=copy.deepcopy(draft);review=api.validate(draft)
        self.assertEqual(draft,before);self.assertFalse(review['committed'])
        with self.assertRaises(ValueError):api.initialize(draft,draft_digest=review['draft_digest'],
            review_digest=review['review_digest'],campaign_id='draft-test',explicitly_accepted=False)
        world=api.initialize(draft,draft_digest=review['draft_digest'],review_digest=review['review_digest'],
            campaign_id='draft-test',explicitly_accepted=True)
        self.assertEqual(world.s['binding']['campaign_profile'],'rise')
        self.assertEqual(world.s['player_actor_ids'],['founder'])
        self.assertEqual(draft,before)

    def test_invalid_fields_and_stale_review_are_rejected(self):
        draft=self.draft();review=api.validate(draft);draft['choices']['supplies']='stocked'
        with self.assertRaises(ValueError):api.initialize(draft,draft_digest=review['draft_digest'],
            review_digest=review['review_digest'],campaign_id='draft-test',explicitly_accepted=True)
        for key,value in [('script','run'),('classification','historical'),('profile_id','unknown')]:
            bad=self.draft();bad[key]=value
            with self.assertRaises(ValueError):api.validate(bad)
            self.assertEqual(api.inspect(bad)['status'],'invalid')
            self.assertFalse(api.inspect(bad)['committed'])


if __name__=='__main__':unittest.main()
