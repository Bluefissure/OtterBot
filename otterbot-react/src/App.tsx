import { Admin, Resource } from 'react-admin';
// import restProvider from 'ra-data-simple-rest';
import fakeDataProvider from 'ra-data-fakerest';
import { PostList, PostEdit, PostCreate, PostIcon } from './posts';

import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';


const dataProvider = fakeDataProvider({
    qqbots: [
      { id: 0, user_id: '306401806', owner: '306401806', name: '獭獭1号' },
      { id: 1, user_id: '306401806', owner: '306401806', name: '獭獭2号' },
      { id: 2, user_id: '306401806', owner: '306401806', name: '獭獭3号' },
    ],
    comments: [
      { id: 0, post_id: 0, author: 'Bluefissure', body: 'Sensational!' },
      { id: 1, post_id: 0, author: 'Bluefissure', body: 'I agree' },
    ],
})


function App() {
  return (
    <Admin dataProvider={dataProvider}>
        <Resource 
          name="qqbots"
          list={PostList}
          edit={PostEdit}
          create={PostCreate}
          icon={PostIcon}
        />
    </Admin>
    );
}

export default App;
