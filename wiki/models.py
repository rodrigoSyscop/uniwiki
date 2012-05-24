from django.db import models

class News(models.Model):
	pub_date = models.DateTimeField()
	headline = models.CharField(max_length=200)
	content  = models.TextField()
	photo    = models.ImageField(upload_to='/photos/')

	class Meta:
		ordering = ["-pub_date"]
		verbose_name_plural = "news"

	def __unicode__(self):
		return self.headline