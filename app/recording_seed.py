"""Exact Generative AI recording curriculum seed."""
from app.extensions import db
from app.models.course import Course
from app.models.video import Video
from app.models.user import User


RECORDING_URLS = [
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=42f856b10068508ddf4588a3023bef7456e181295565331cd65db60ec99c1675&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=bf438945b9debc524504a05bb76bcbf36ef02efbb15c47506b2ec0f345d5326c&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=f28f9dc2c35b624233ee2ebaca9da216f93e5eedd09b3cb32d66562ec73254f8&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=ae267cea6da710c469d28d65f3f52f86044aff86322562711b7767bcdbcac418&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=30a288dcb9ee8f56b718c37e52475e5b9e2b05059850669360617659848e6d3b&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=72e9f45d4fc788c9e28994fe847cf8885b018f5bc005272c5fbf12e083e14e66&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=069c210812ae7591e58ec874ad442c04bc7c5d291fe9b54334549389666c6618&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=4912ff46a284236ee5f8ec0e1c291f8125ba62b2f1552f8b6901ea3551886259&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=d031aebe4e7a609e37cc328724dc9e32ccd691495d42e359f3217e4adc19d429&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=bfc0741cd578b40696291bc6f72ba8fdaca30e0a7c6e9ab30913b9e8865e7ac8&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=5d3f1cdb0da776d82ab7dce7f3bf8b307ab33c493224991dbee9e651197ee42f&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=83f60d4b9299ae89579003c7fad94e488907ed5628a30e15eb0c7f7856c10738&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=e978c76015589e7d460335411b50438f5dc5222ecabfb35114f09525c3d2f468&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=3c7e7c5567b57a52d0a442b4f81b632504b175d458b94101aabe7235d79602bd&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=db75838461decdf4ed7d82ec3b4160469075065a3afb737ca9feba3868ad95a9&x-meeting-org=20108692076',
    'https://meetinglab.zoho.eu/meeting/videoprv?recordingId=557b84ae9ac8e5a96829b4a98371a907ee103a3e3a4e4c7c8c2bf4bcd48307af&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=3b000586a19809bb8d706d71ebab41f00c02597e96e68e32030edc762c627fa2&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=a0b9865dd514b8780c4a9cf0e6eeccd20ed4b9050c06e91c2e02b458ad557031&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=90144b0f5d287c538233cd1c2d9cbd642e06a23c2c5c38902ab944e44ddaddff&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/videoprv?recordingId=59a14a804872f848f2c6550245bc711412e9bd7460fe6f65f19c0a779ac1fad9&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=420ae7a0ca5b145e06a5e2b5a5cb4b0ce7b699717527701f6d3113ee8c032a&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=8d929738a580f07cdfc40a3a5ff02f03a4dd395818c1b7a5590a2480123561bb&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=c1f616aa16d384650571b6e8cfc13daae7c2739688ec6037a0c8bb891c2a070e&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=e9124ed1739806836f935b650e52b61d4a7260fd12a874e6bc7c0006a5f89c5f&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=e9124ed1739806836f935b650e52b61d4a7260fd12a874e6bc7c0006a5f89c5f&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=b153859f502454a8cabb2932182a7e21920cc0423f5fe123e1a3efcfe024bf75&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=15c0f9c4374175b7261c18fc59aac2d4c20c05dfee5b8493fada55c65fdbb732&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=238ab4a1bb0d9bd5867f0a07177c3cbd5c3ad0470e48901e79a252ee3de68f77&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=53e24cf863b9ae461514281f527df4a396bac4823fc346be7262a8b0c69363be&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=4a22642c03ce54a4d3b5b4c3351765c78f4e95138d8a9863cd276e471a6c9455&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=2860c5e7d1b913ebaacc1ca1b86046424554a7b57f950199a72f56ad6344b113&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=2860c5e7d1b913ebaacc1ca1b86046424554a7b57f950199a72f56ad6344b113&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=dd9eaee1badbe8ffb158cf04a5a049f295813ba2e944830461de9a31e3af8d3e&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=e0ebb567f924f127a4c4fa8710f760179151048adde3fd461e369052856d40de&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=e0ebb567f924f127a4c4fa8710f760179151048adde3fd461e369052856d40de&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=117d7b4415d425030e550b5f3a232b317fb07cd958fdf2f7401d1d88ee3d6899&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=1274a60aee022892d07abe5b96227d427e63705a56f99698ad878ec1037a8c97&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=6df4ff9c890ae3a05e384790286c2ea14ca4fac062704c4aac4179fa07a23a44&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=ae9380a0752af7d0abd25ccbdf1baff72d4553a27bf22e0706cfa1f5091d14dd&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=ae9380a0752af7d0abd25ccbdf1baff72d4553a27bf22e0706cfa1f5091d14dd&x-meeting-org=20108692076',
    'https://meeting.zoho.eu/meeting/public/videoprv?recordingId=eb2698e9adc1f4a1ab125883d68e2d11edcb8ac1103c97c97d2af4e1eb2cc496&x-meeting-org=20108692076',
]


def seed_generative_ai_recordings():
    course = Course.query.filter_by(name='Generative AI').first()
    if not course:
        raise RuntimeError('Generative AI course does not exist.')
    mentor = User.query.filter_by(role='mentor_admin').first()
    for video in course.videos.all():
        db.session.delete(video)
    db.session.flush()
    for day_number, url in enumerate(RECORDING_URLS, start=1):
        db.session.add(Video(
            title=f'Day {day_number}', description='', url=url,
            course_id=course.id, day_number=day_number,
            order_index=day_number, resource_type='video',
            status='published', created_by=mentor.id if mentor else None,
        ))
    db.session.commit()
