from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets, StringField
from wtforms.validators import DataRequired
import models


class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(",")]
            if self.remove_duplicates:
                self.data = list(set(self.data))

    def _value(self):
        if self.data:
            return ", ".join(tag.name if isinstance(tag, models.Tag) else tag for tag in self.data)
        return ""

BaseNoteForm = model_form(
    models.Note, base_class=FlaskForm, exclude=["created_date", "updated_date"], db_session=models.db.session
)

class NoteForm(BaseNoteForm):
    tags = TagListField("Tag")