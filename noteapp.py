import flask
import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)

def refresh_tags(note):
    db = models.db
    db.session.refresh(note)
    return note

@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template("index.html", notes=notes)

@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        return flask.render_template("notes-create.html", form=form)
    
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name)).scalars().first()
        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)
        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    if not note:
        return flask.redirect(flask.url_for("index"))

    form = forms.NoteForm(obj=note)

    if form.validate_on_submit():

        note.description = form.description.data
        note.title = form.title.data
        # note.content = form.content.data

        # จัดการกับแท็ก
        note.tags.clear()  # ลบแท็กที่มีอยู่
        if isinstance(form.tags.data, str):
            tag_names = [tag_name.strip() for tag_name in form.tags.data.split(',') if tag_name.strip()]
        else:
            # ถ้า form.tags.data เป็น list แทนที่นี่
            tag_names = [tag_name.strip() for tag_name in form.tags.data if tag_name.strip()]

        for tag_name in tag_names:
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalars().first()

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)  # เพิ่ม Tag objects

        db.session.commit()  # บันทึกการเปลี่ยนแปลง
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-edit.html", form=form, note=note)

@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()

    if note:
        db.session.delete(note)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/<int:note_id>/tags/<int:tag_id>/delete", methods=["POST"])
def delete_tag(note_id, tag_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()
    tag = db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id)).scalars().first()

    if note and tag:
        if tag in note.tags:
            note.tags.remove(tag)
            db.session.commit()

    return flask.redirect(flask.url_for("notes_edit", note_id=note.id))

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

if __name__ == "__main__":
    app.run(debug=True)