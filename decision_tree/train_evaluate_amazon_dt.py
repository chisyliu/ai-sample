
import numpy as np
import nltk
from utils.read_dataset import read_amazon_csv
import re
import pickle
import os.path

REGEX = re.compile("([\w][\w']*\w)")


def tokenize(text):
    """
    It tokenizes the given text
    :param text:
    :return: a list of words in the text
    """

    return [tok.strip().lower() for tok in REGEX.findall(text)]


def get_features(data_list, label_list, feature_size=500, op_type=''):

    """
    Returns a feature vector after feature selection
    :param data_list: contains the review text
    :param label_list: contains the classified review rating
    :param feature_size: the size of the feature vector
    :param op_type: the type of operation performed
    :return: feature vector of size feature_size
    """

    r1_indices = np.where(label_list == '1')
    r2_indices = np.where(label_list == '2')
    r3_indices = np.where(label_list == '3')
    r4_indices = np.where(label_list == '4')
    r5_indices = np.where(label_list == '5')

    l_data_list = np.array([])

    if os.path.exists(dir_path + '/../resources/'+op_type+ 'amazon_datalist'):
        with open(dir_path + '/../resources/'+op_type+ 'amazon_datalist', "rb") as f:
            l_data_list = pickle.load(f)
            print('data list is loaded ...')
    else:
        with open(dir_path + '/../resources/'+op_type+ 'amazon_datalist', "wb") as f:

            from nltk.corpus import stopwords
            for each_row in data_list:

                new_cell_contents = ''
                cell_dup = []

                for each_cell in each_row:
                    if type(each_cell) is str:
                        '''
                            Changing to lower case
                        '''
                        words = nltk.word_tokenize(each_cell.lower())
                        words = [word.lower() for word in words if word.isalpha()]

                        '''
                            Stemming the words
                        '''
                        from nltk.stem.snowball import SnowballStemmer
                        stemmer = SnowballStemmer('english')
                        words = [stemmer.stem(word) for word in words]

                        '''
                            Removing stop words
                        '''

                        cell_contents = [word for word in words if word not in stopwords.words('english')]

                        for each_word in cell_contents:
                            if each_word not in cell_dup:
                                cell_dup.append(each_word)
                                new_cell_contents = new_cell_contents + ' ' +each_word

                        new_cell_contents = new_cell_contents.strip()

                l_data_list = np.append(l_data_list, np.array([new_cell_contents]), axis=0)
            pickle.dump(l_data_list, f)

    '''
        Selecting the features
    '''

    if op_type == '' and not os.path.exists(dir_path + '/../resources/vocabulary_1000'):
        with open(dir_path + '/../resources/vocabulary_1000', "wb") as f:
            vocabulary = dict()

            # For rating 1
            new_dic = get_word_freq(l_data_list, r1_indices, feature_size / 5)
            vocabulary = {**vocabulary, **new_dic}

            # For rating 2
            new_dic = get_word_freq(l_data_list, r2_indices, feature_size / 5)
            vocabulary = {**vocabulary, **new_dic}

            # For rating 3
            new_dic = get_word_freq(l_data_list, r3_indices, feature_size / 5)
            vocabulary = {**vocabulary, **new_dic}

            # For rating 4
            new_dic = get_word_freq(l_data_list, r4_indices, feature_size / 5)
            vocabulary = {**vocabulary, **new_dic}

            # For rating 5
            new_dic = get_word_freq(l_data_list, r5_indices, feature_size / 5)
            vocabulary = {**vocabulary, **new_dic}

            vocabulary = {each_key: index for each_key, index in
                          zip(vocabulary.keys(), range(0, len(vocabulary.keys())))}

            pickle.dump(vocabulary,f)
            print('vocabulary is created ... ')
    else:
        with open(dir_path + '/../resources/vocabulary_1000', "rb") as f:
            vocabulary = pickle.load(f)
            print('vocabulary is loaded...')

    from sklearn.feature_extraction.text import CountVectorizer
    vectorizer = CountVectorizer(tokenizer=tokenize, vocabulary=vocabulary)
    vectorizer._validate_vocabulary()
    print(vectorizer.get_feature_names())
    features = vectorizer.fit_transform(l_data_list)
    features = features.toarray()

    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(vocabulary=vocabulary, min_df=0.4, max_df=0.9)
    weightVector = vectorizer.fit_transform(features)
    weightVector = weightVector.toarray()
    return weightVector


def get_word_freq(data_list, r_indices, feature_size):

    """
    It returns the word frequencies of the text
    :param data_list: the text review
    :param r_indices: indices to be considered for calculating the word frequencies
    :param feature_size: size of the feature vector
    :return: words along with their frequencies
    """

    r_data_list = []
    for each_index in r_indices[0]:
        r_data_list = r_data_list + re.findall(r'\w+', data_list[each_index])
    from collections import Counter
    t = Counter(r_data_list).most_common(int(feature_size))
    vocabulary = dict((x, y) for x, y in t)
    return vocabulary

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))

    feature_list, label_list = read_amazon_csv(dir_path + '/../dataset/amazon_dataset/amazon_baby_test.csv')

    from sklearn.model_selection import train_test_split
    feature_train, feature_test, label_train, label_test = train_test_split(
        feature_list , label_list, train_size=0.90)

    f_size = 1000
    if not os.path.exists(dir_path+ '/../resources/rec_features_1000'):
        p_feature_train = get_features(feature_train,label_train, feature_size=f_size)

        with open(dir_path+'/../resources/rec_features_1000', "wb") as f:
            pickle.dump(p_feature_train, f)

        print('pickle created for features in training set...')

    else:
        with open(dir_path+'/../resources/rec_features_1000','rb') as f:
            p_feature_train = pickle.load(f)

        print('pickle loaded for training features...')

    '''
        Training the decision tree
    '''
    if not os.path.exists(dir_path + dir_path + '/../resources/decision_tree_clf'):
        from sklearn.tree import DecisionTreeClassifier
        clf = DecisionTreeClassifier(min_samples_split=100, max_depth=100)

        clf.fit(p_feature_train, label_train)
        with open(dir_path + '/../resources/decision_tree_clf', "wb") as f:
            pickle.dump(clf, f)

        print('pickle created for model...')

    else:
        with open(dir_path + '/../resources/decision_tree_clf','rb') as f:
            clf = pickle.load(f)

        print('pickle loaded for model...')

    test_features = get_features(feature_test, label_test, feature_size=f_size, op_type='test')
    label_predict = clf.predict(test_features)

    from sklearn.metrics import precision_score
    precision = precision_score(label_test, label_predict, average='weighted')

    from sklearn.metrics import recall_score
    recall = recall_score(label_test, label_predict, average='weighted')

    f1 = 2 * (precision * recall) / (precision + recall)

    from sklearn.metrics import accuracy_score
    accuracy = accuracy_score(label_test, label_predict)

    print(str(precision) + '\t' + str(recall) + '\t' + str(f1) + '\t' + str(accuracy))
