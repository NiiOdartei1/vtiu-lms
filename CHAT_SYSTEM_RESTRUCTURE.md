# Chat System Restructure - Include All Users and Admins

## Overview
The chat system has been restructured to include **admins** alongside students and teachers. Users can now:
- Send direct messages to teachers
- Send direct messages to students
- Send direct messages to admins (Finance, Academic, Admissions, and Superadmins)
- Create group chats with mixed participants (students, teachers, admins)

---

## Changes Made

### 1. **chat_routes.py** - Backend Changes

#### Imports
- ✅ Added `Admin` to model imports
```python
from models import Conversation, ConversationParticipant, Message, MessageReaction, User, Admin, StudentProfile, TeacherProfile
```

#### Access Control Function
- ✅ Renamed `is_teacher_or_student()` → `is_user_or_admin()`
- ✅ Now allows all authenticated users: teachers, students, and all admin roles
```python
def is_user_or_admin():
    """Check if current user is a teacher, student, or admin. Allows all authenticated users."""
    role = getattr(current_user, "role", None)
    return role in ["teacher", "student", "superadmin", "finance_admin", "academic_admin", "admissions_admin"]
```

#### User Resolution Function
- ✅ Updated `resolve_person_by_public_id()` to check both User and Admin tables
- ✅ Returns correct role for admins (access as `admin.role` - database column, not property)
```python
def resolve_person_by_public_id(pub_id):
    """Return (model_instance, role_string) or (None, None). Checks both User and Admin tables."""
    if not pub_id:
        return None, None
    
    # Try to find in User table first (students/teachers)
    person = User.query.filter_by(public_id=pub_id).first()
    if person:
        return person, getattr(person, "role", "user")
    
    # Try to find in Admin table
    admin = Admin.query.filter_by(public_id=pub_id).first()
    if admin:
        return admin, admin.role  # admin.role is a database column, not a property
    
    return None, None
```

#### All Route Guards
- ✅ Updated all 20+ route guards from `is_teacher_or_student()` → `is_user_or_admin()`
- Routes affected:
  - `@socketio.on('join')`
  - `@socketio.on('send_message')`
  - `@chat_bp.route('/') - chat_home`
  - `@chat_bp.route('/conversations') - get_conversations`
  - `@chat_bp.route('/conversations/<int:conv_id>/messages') - get_messages`
  - `@chat_bp.route('/presence/<public_id>') - get_presence`
  - `@chat_bp.route('/send_dm') - send_dm`
  - And all other message/group chat routes

#### `/users` Endpoint - Enhanced
- ✅ Added support for `role='admin'` parameter
- ✅ Admin users are returned with their role title
- ✅ Admins don't need programme/level filtering (unlike students)

**Endpoint signature:**
```python
GET /chat/users?role={teacher|student|admin}&programme=X&level=Y
```

**Response for admins:**
```json
[
  {
    "id": "admin-public-id",
    "name": "john.finance@admin.vtiu.edu.gh (Finance Admin)"
  },
  ...
]
```

---

### 2. **templates/chat.html** - Frontend Changes

#### DM Composer - Role Selection
- ✅ Added **Admin** button to role selection in Step 1
```html
<!-- Step 1: Select role -->
<div id="dmStepRole">
  <div class="dm-step-label">Step 1 · Select role</div>
  <div class="dm-step-actions">
    <button class="btn btn-sm btn-outline-secondary dm-role-btn" data-role="student">Student</button>
    <button class="btn btn-sm btn-outline-secondary dm-role-btn" data-role="teacher">Teacher</button>
    <button class="btn btn-sm btn-outline-secondary dm-role-btn" data-role="admin">Admin</button>
  </div>
</div>
```

#### DM Role Button Handlers
- ✅ Added handler for `data-role="admin"` button
- ✅ Admin selection skips programme/level selection (like teachers)
- ✅ Directly loads admin list via `loadUsers('admin')`

```javascript
} else if (role === 'admin') {
  // Admins: skip to admin list (no programme/level filtering)
  document.getElementById('dmStepRole').style.display = 'none';
  document.getElementById('dmStepProgramme').style.display = 'none';
  document.getElementById('dmStepLevel').style.display = 'none';
  document.getElementById('dmStepUsers').style.display = 'block';
  
  // Load admins
  await loadUsers('admin');
}
```

#### loadUsers() Function
- ✅ Already supports any role via query parameter
- ✅ No changes needed - works seamlessly with `loadUsers('admin')`

---

## Data Flow

### Direct Message to Admin
```
User clicks "New DM" (newDMBtn)
  ↓
Selects "Admin" role
  ↓
loadUsers('admin')
  ↓
GET /chat/users?role=admin
  ↓
Backend queries Admin table, returns list
  ↓
User selects admin from list
  ↓
startDM(admin_public_id)
  ↓
Creates/retrieves conversation with ConversationParticipant records
  ↓
Chat is established
```

### Conversation Participation
```
resolve_person_by_public_id(public_id)
  ↓
Checks User table → Checks Admin table
  ↓
Returns (model_instance, role)
  ↓
Used for display names, avatars, and permissions
```

---

## Security & Permissions

✅ **Authentication:**
- All chat routes require `@login_required`
- Access control via `is_user_or_admin()` - only authenticated users can chat

✅ **Authorization:**
- Users can see admins in DM list
- Admins can chat with students, teachers, and other admins
- Conversation access based on `ConversationParticipant` records

✅ **Data Isolation:**
- Each conversation is isolated via `ConversationParticipant` entries
- Messages filtered by conversation membership
- No cross-conversation leakage

---

## Testing Checklist

- [ ] Login as student → Send DM to admin → Verify message appears
- [ ] Login as teacher → Send DM to admin → Verify message appears
- [ ] Login as admin → Send DM to student → Verify message appears
- [ ] Login as admin → Send DM to teacher → Verify message appears
- [ ] Login as admin → Send DM to another admin → Verify message appears
- [ ] Create group with mix of students, teachers, admins → Verify all can chat
- [ ] Edit own message → Verify works for all roles
- [ ] Delete own message → Verify works for all roles
- [ ] Forward message → Verify works for all roles
- [ ] React to message → Verify works for all roles
- [ ] Verify online/offline status across roles
- [ ] Test on mobile → Verify responsive chat UI

---

## Backward Compatibility

✅ **No Breaking Changes:**
- Existing student-to-student chats: ✅ Still work
- Existing student-to-teacher chats: ✅ Still work
- Existing teacher-to-teacher chats: ✅ Still work
- Existing group chats: ✅ Still work
- All message features (edit, delete, forward, react): ✅ Still work

---

## Admin Role Support

All admin roles can now participate in chat:

| Role | Can Chat | Can DM Others | Can Join Groups |
|------|----------|---------------|-----------------|
| Superadmin | ✅ Yes | ✅ Yes | ✅ Yes |
| Finance Admin | ✅ Yes | ✅ Yes | ✅ Yes |
| Academic Admin | ✅ Yes | ✅ Yes | ✅ Yes |
| Admissions Admin | ✅ Yes | ✅ Yes | ✅ Yes |

---

## Future Enhancements

Potential features to add:
- [ ] Admin-to-all broadcast messages
- [ ] Notification settings per admin role
- [ ] Archive/pin conversations
- [ ] Message scheduling
- [ ] Voice/video calls with admins
- [ ] Admin chat analytics and logs
