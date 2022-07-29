import { List, Datagrid, Edit, Create, SimpleForm, DateField, TextField, EditButton, TextInput, DateInput } from 'react-admin';
import BookIcon from '@mui/icons-material/Book';
export const PostIcon = BookIcon;

export const PostList = () => (
    <List>
        <Datagrid>
            {/* <TextField source="id" /> */}
            <TextField source="user_id" label="Bot ID"/>
            <TextField source="name" />
            <TextField source="owner" />
            {/* <TextField source="title" />
            <DateField source="published_at" />
            <TextField source="average_note" />
            <TextField source="views" /> */}
            <EditButton />
        </Datagrid>
    </List>
);

const PostTitle = ({ record } : { record?: {title: string} }) => {
    return <span>Post {record ? `"${record.title}"` : ''}</span>;
};

export const PostEdit = () => (
    <Edit title={<PostTitle />}>
        <SimpleForm>
            {/* <TextInput disabled source="id" /> */}
            <TextInput source="user_id" />
            <TextInput source="name" />
            <TextInput source="owner" />
            {/* <TextInput multiline source="body" />
            <DateInput label="Publication date" source="published_at" />
            <TextInput source="average_note" />
            <TextInput disabled label="Nb views" source="views" /> */}
        </SimpleForm>
    </Edit>
);

export const PostCreate = () => (
    <Create title="Create a Post">
        <SimpleForm>
            <TextInput source="title" />
            <TextInput source="teaser" options={{ multiline: true }} />
            <TextInput multiline source="body" />
            <TextInput label="Publication date" source="published_at" />
            <TextInput source="average_note" />
        </SimpleForm>
    </Create>
);